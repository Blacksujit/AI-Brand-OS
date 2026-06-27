from __future__ import annotations

import time
import uuid
from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter
from starlette.middleware.base import BaseHTTPMiddleware

from core.config import Settings
from core.logging import get_logger

logger = get_logger(__name__)


def build_rate_limiter(settings: Settings) -> Limiter:
    if settings.rate_limit_enabled:
        return Limiter(key_func=lambda r: r.client.host if r.client else "unknown")
    return Limiter(key_func=lambda r: r.client.host if r.client else "unknown", enabled=False)


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        rid = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = rid
        response = await call_next(request)
        response.headers["X-Request-ID"] = rid
        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        start = time.monotonic()
        method = request.method
        path = request.url.path
        query = str(request.url.query) if request.url.query else ""
        client_ip = request.client.host if request.client else "unknown"
        rid = getattr(request.state, "request_id", "")

        response = await call_next(request)

        elapsed = (time.monotonic() - start) * 1000

        logger.info(
            "request_completed",
            method=method,
            path=path,
            query=query or None,
            status=response.status_code,
            duration_ms=round(elapsed, 1),
            client_ip=client_ip,
            request_id=rid,
        )

        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "0"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=(), interest-cohort=()"
        )
        return response


class MaxBodySizeMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_size: int = 1_048_576) -> None:
        super().__init__(app)
        self.max_size = max_size

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.max_size:
            from fastapi.responses import JSONResponse

            return JSONResponse(
                status_code=413,
                content={"detail": "Request body too large"},
            )

        body = await request.body()
        if len(body) > self.max_size:
            from fastapi.responses import JSONResponse

            return JSONResponse(
                status_code=413,
                content={"detail": "Request body too large"},
            )

        return await call_next(request)


def register_cors(app: FastAPI, settings: Settings) -> None:
    origins = settings.cors_origins
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=[
            "Authorization",
            "Content-Type",
            "Accept",
            "Origin",
            "X-Request-ID",
        ],
    )


def register_middleware(app: FastAPI, settings: Settings) -> None:
    app.add_middleware(MaxBodySizeMiddleware, max_size=settings.max_request_body_size)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(RequestLoggingMiddleware)
