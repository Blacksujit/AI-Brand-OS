from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import router as v1_router
from app.core.cache import CacheService, get_cache
from app.core.config import Settings, get_settings
from app.core.db import Database, get_db
from app.core.logging import configure_logging, get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    configure_logging(settings)

    db = get_db(settings)
    cache = get_cache(settings)

    await db.initialize()
    await cache.initialize()

    app.state.db = db
    app.state.cache = cache

    logger.info(
        "application_started",
        env=settings.env,
        debug=settings.debug,
    )
    yield

    await cache.close()
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
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(v1_router)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "version": "0.1.0"}
