from __future__ import annotations

import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from api.v1.router import router as v1_router
from core.config import get_settings
from core.logging import configure_logging, get_logger
from core.middleware import build_rate_limiter, register_cors, register_middleware
from database import Database, get_db

logger = get_logger(__name__)

_start_time: float = 0.0


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    global _start_time
    settings = get_settings()
    configure_logging(settings)

    db = get_db(settings)
    await db.initialize()
    app.state.db = db

    _start_time = time.time()

    logger.info("application_started", env=settings.env, debug=settings.debug)
    yield

    await db.close()
    logger.info("application_stopped")


app = FastAPI(
    title="BrandOS API",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs" if get_settings().is_development else None,
    redoc_url="/redoc" if get_settings().is_development else None,
)

settings = get_settings()

limiter = build_rate_limiter(settings)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error(
        "unhandled_exception",
        path=request.url.path,
        method=request.method,
        error=str(exc),
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


register_cors(app, settings)
register_middleware(app, settings)
app.add_middleware(SlowAPIMiddleware)

app.include_router(v1_router)


@app.get("/health")
async def health(request: Request) -> dict:
    db: Database = request.app.state.db
    db_health = await db.health_check()
    uptime_seconds = time.time() - _start_time

    return {
        "status": "healthy" if db_health["status"] == "healthy" else "degraded",
        "version": "0.1.0",
        "env": settings.env,
        "uptime_seconds": round(uptime_seconds, 1),
        "database": db_health,
    }
