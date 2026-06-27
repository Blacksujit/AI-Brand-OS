from __future__ import annotations

from typing import ClassVar
from unittest.mock import MagicMock

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from httpx import ASGITransport, AsyncClient
from slowapi import Limiter
from starlette.requests import Request

from core.middleware import (
    MaxBodySizeMiddleware,
    RequestIDMiddleware,
    RequestLoggingMiddleware,
    SecurityHeadersMiddleware,
    build_rate_limiter,
    register_cors,
    register_middleware,
)

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _app(*middleware) -> FastAPI:
    """Build a tiny app with given middleware and a GET /ping route."""
    app = FastAPI()

    for cls, kwargs in middleware:
        app.add_middleware(cls, **kwargs)

    @app.get("/ping")
    async def ping() -> dict[str, str]:
        return {"ok": "pong"}

    @app.post("/body")
    async def read_body(request: Request) -> dict[str, str]:
        body = await request.body()
        return {"received": body.decode()}

    return app


# ---------------------------------------------------------------------------
# RequestIDMiddleware
# ---------------------------------------------------------------------------


class TestRequestIDMiddleware:
    async def test_sets_request_id_on_response(self) -> None:
        app = _app((RequestIDMiddleware, {}))
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/ping")

        assert resp.status_code == 200
        assert "X-Request-ID" in resp.headers
        assert len(resp.headers["X-Request-ID"]) > 0

    async def test_respects_incoming_request_id(self) -> None:
        app = _app((RequestIDMiddleware, {}))
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/ping", headers={"X-Request-ID": "my-trace-42"})

        assert resp.status_code == 200
        assert resp.headers["X-Request-ID"] == "my-trace-42"

    async def test_each_request_gets_unique_id(self) -> None:
        app = _app((RequestIDMiddleware, {}))
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp1 = await client.get("/ping")
            resp2 = await client.get("/ping")

        assert resp1.headers["X-Request-ID"] != resp2.headers["X-Request-ID"]

    async def test_request_id_on_post(self) -> None:
        app = _app((RequestIDMiddleware, {}))
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post("/body", content="hello")

        assert resp.status_code == 200
        assert "X-Request-ID" in resp.headers


# ---------------------------------------------------------------------------
# SecurityHeadersMiddleware
# ---------------------------------------------------------------------------


class TestSecurityHeadersMiddleware:
    EXPECTED: ClassVar[dict[str, str]] = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "0",
        "Referrer-Policy": "strict-origin-when-cross-origin",
    }

    async def test_sets_all_security_headers(self) -> None:
        app = _app((SecurityHeadersMiddleware, {}))
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/ping")

        for header, expected in self.EXPECTED.items():
            assert resp.headers.get(header) == expected, f"missing/incorrect {header}"

    async def test_permissions_policy_header(self) -> None:
        app = _app((SecurityHeadersMiddleware, {}))
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/ping")

        pp = resp.headers.get("Permissions-Policy")
        assert pp is not None
        assert "camera=()" in pp
        assert "microphone=()" in pp
        assert "geolocation=()" in pp
        assert "interest-cohort=()" in pp


# ---------------------------------------------------------------------------
# MaxBodySizeMiddleware
# ---------------------------------------------------------------------------


class TestMaxBodySizeMiddleware:
    async def test_allows_normal_sized_body(self) -> None:
        app = _app((MaxBodySizeMiddleware, {"max_size": 1_048_576}))
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post("/body", content="small")

        assert resp.status_code == 200

    async def test_rejects_oversized_body_via_content_length(self) -> None:
        app = _app((MaxBodySizeMiddleware, {"max_size": 10}))
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post("/body", content="x" * 100)

        assert resp.status_code == 413
        assert resp.json()["detail"] == "Request body too large"

    async def test_rejects_oversized_body_via_actual_size(self) -> None:
        app = _app((MaxBodySizeMiddleware, {"max_size": 10}))
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                "/body",
                content="x" * 100,
                headers={"content-length": "5"},
            )

        assert resp.status_code == 413
        assert resp.json()["detail"] == "Request body too large"

    async def test_allows_empty_body(self) -> None:
        app = _app((MaxBodySizeMiddleware, {"max_size": 1_048_576}))
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post("/body", content=b"")

        assert resp.status_code == 200

    async def test_get_request_no_body_passes(self) -> None:
        app = _app((MaxBodySizeMiddleware, {"max_size": 1}))
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/ping")

        assert resp.status_code == 200

    async def test_body_just_under_limit_passes(self) -> None:
        app = _app((MaxBodySizeMiddleware, {"max_size": 100}))
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post("/body", content="a" * 99)

        assert resp.status_code == 200

    async def test_body_at_limit_passes(self) -> None:
        app = _app((MaxBodySizeMiddleware, {"max_size": 100}))
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post("/body", content="a" * 100)

        assert resp.status_code == 200

    async def test_body_one_over_limit_fails(self) -> None:
        app = _app((MaxBodySizeMiddleware, {"max_size": 100}))
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post("/body", content="a" * 101)

        assert resp.status_code == 413


# ---------------------------------------------------------------------------
# RequestLoggingMiddleware
# ---------------------------------------------------------------------------


class TestRequestLoggingMiddleware:
    async def test_does_not_crash_with_request_id(self) -> None:
        app = FastAPI()
        app.add_middleware(RequestIDMiddleware)
        app.add_middleware(RequestLoggingMiddleware)

        @app.get("/ping")
        async def ping() -> dict[str, str]:
            return {"ok": "pong"}

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/ping")

        assert resp.status_code == 200

    async def test_does_not_crash_without_request_id(self) -> None:
        app = FastAPI()
        app.add_middleware(RequestLoggingMiddleware)

        @app.get("/ping")
        async def ping() -> dict[str, str]:
            return {"ok": "pong"}

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/ping")

        assert resp.status_code == 200

    async def test_logs_with_query_string(self) -> None:
        app = FastAPI()
        app.add_middleware(RequestLoggingMiddleware)

        @app.get("/search")
        async def search() -> dict[str, str]:
            return {"ok": "pong"}

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/search?q=hello&page=1")

        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# build_rate_limiter
# ---------------------------------------------------------------------------


class TestBuildRateLimiter:
    def test_returns_limiter_when_enabled(self) -> None:
        settings = MagicMock()
        settings.rate_limit_enabled = True

        limiter = build_rate_limiter(settings)

        assert isinstance(limiter, Limiter)

    def test_returns_limiter_with_enabled_true(self) -> None:
        settings = MagicMock()
        settings.rate_limit_enabled = True

        limiter = build_rate_limiter(settings)

        assert limiter.enabled is True

    def test_returns_disabled_limiter(self) -> None:
        settings = MagicMock()
        settings.rate_limit_enabled = False

        limiter = build_rate_limiter(settings)

        assert isinstance(limiter, Limiter)
        assert limiter.enabled is False

    def test_key_func_returns_unknown_when_no_client(self) -> None:
        settings = MagicMock()
        settings.rate_limit_enabled = True
        limiter = build_rate_limiter(settings)
        fake_request = MagicMock()
        fake_request.client = None

        key = limiter._key_func(fake_request)  # noqa: SLF001

        assert key == "unknown"

    def test_key_func_uses_client_host(self) -> None:
        settings = MagicMock()
        settings.rate_limit_enabled = True
        limiter = build_rate_limiter(settings)
        fake_request = MagicMock()
        fake_request.client.host = "10.0.0.1"

        key = limiter._key_func(fake_request)  # noqa: SLF001

        assert key == "10.0.0.1"


# ---------------------------------------------------------------------------
# register_cors
# ---------------------------------------------------------------------------


class TestRegisterCors:
    def test_adds_cors_middleware(self) -> None:
        app = FastAPI()
        settings = MagicMock()
        settings.cors_origins = ["http://localhost:3000"]
        settings.cors_allow_credentials = True

        register_cors(app, settings)

        cls_list = [m.cls for m in app.user_middleware]
        assert CORSMiddleware in cls_list

    def test_cors_origins_from_settings(self) -> None:
        app = FastAPI()
        origins = ["http://example.com"]
        settings = MagicMock()
        settings.cors_origins = origins
        settings.cors_allow_credentials = False

        register_cors(app, settings)

        mw = [m for m in app.user_middleware if m.cls is CORSMiddleware]
        assert len(mw) == 1
        assert mw[0].kwargs["allow_origins"] == origins
        assert mw[0].kwargs["allow_credentials"] is False

    def test_cors_allow_credentials(self) -> None:
        app = FastAPI()
        settings = MagicMock()
        settings.cors_origins = ["*"]
        settings.cors_allow_credentials = True

        register_cors(app, settings)

        mw = [m for m in app.user_middleware if m.cls is CORSMiddleware]
        assert mw[0].kwargs["allow_credentials"] is True


# ---------------------------------------------------------------------------
# register_middleware
# ---------------------------------------------------------------------------


class TestRegisterMiddleware:
    def test_adds_all_middleware(self) -> None:
        app = FastAPI()
        settings = MagicMock()
        settings.max_request_body_size = 1024

        register_middleware(app, settings)

        cls_list = [m.cls for m in app.user_middleware]
        assert len(cls_list) >= 4
        assert MaxBodySizeMiddleware in cls_list
        assert SecurityHeadersMiddleware in cls_list
        assert RequestIDMiddleware in cls_list
        assert RequestLoggingMiddleware in cls_list

    def test_passes_max_size_to_body_middleware(self) -> None:
        app = FastAPI()
        settings = MagicMock()
        settings.max_request_body_size = 999

        register_middleware(app, settings)

        mw = [m for m in app.user_middleware if m.cls is MaxBodySizeMiddleware]
        assert len(mw) == 1
        assert mw[0].kwargs["max_size"] == 999


# ---------------------------------------------------------------------------
# Integration — stacked middleware
# ---------------------------------------------------------------------------


class TestMiddlewareIntegration:
    async def test_request_id_and_security_headers_together(self) -> None:
        app = FastAPI()
        settings = MagicMock()
        settings.max_request_body_size = 1_048_576
        register_middleware(app, settings)

        @app.get("/test")
        async def test() -> dict[str, str]:
            return {"ok": "pong"}

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/test", headers={"X-Request-ID": "integration-1"})

        assert resp.status_code == 200
        assert resp.headers["X-Request-ID"] == "integration-1"
        assert resp.headers["X-Content-Type-Options"] == "nosniff"
        assert resp.headers["X-Frame-Options"] == "DENY"

    async def test_middleware_stacked_with_cors(self) -> None:
        app = FastAPI()
        settings = MagicMock()
        settings.max_request_body_size = 1_048_576
        settings.cors_origins = ["http://localhost:3000"]
        settings.cors_allow_credentials = True

        register_cors(app, settings)
        register_middleware(app, settings)

        @app.get("/ping")
        async def ping() -> dict[str, str]:
            return {"ok": "pong"}

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/ping")

        assert resp.status_code == 200
        assert resp.headers["X-Request-ID"]
        assert resp.headers["X-Content-Type-Options"] == "nosniff"
