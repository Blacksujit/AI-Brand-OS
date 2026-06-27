from __future__ import annotations

import time
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from core.config import Settings
from core.logging import get_logger
from models.base import Base

logger = get_logger(__name__)


class Database:
    def __init__(self, settings: Settings) -> None:
        connect_args: dict = {}
        if settings.is_async_sqlite:
            connect_args["check_same_thread"] = False

        engine_kwargs: dict = {
            "echo": settings.debug,
            "pool_pre_ping": True,
            "pool_recycle": settings.database_pool_recycle,
            "json_serializer": _default_json_serializer,
        }
        if connect_args:
            engine_kwargs["connect_args"] = connect_args

        if not settings.is_async_sqlite:
            engine_kwargs["pool_size"] = settings.database_pool_size
            engine_kwargs["max_overflow"] = settings.database_max_overflow
            engine_kwargs["pool_timeout"] = settings.database_pool_timeout

        self.engine = create_async_engine(
            settings.database_url,
            **engine_kwargs,
        )
        self.session_factory = async_sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    async def initialize(self) -> None:
        import models  # noqa: F401 — registers all tables with Base.metadata

        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        await self.verify_connection()
        logger.info(
            "database_initialized",
            url=self._safe_url(),
            pool_size=self._pool_size(),
        )

    async def close(self) -> None:
        await self.engine.dispose()
        logger.info("database_disposed")

    async def verify_connection(self) -> bool:
        try:
            async with self.session() as session:
                result = await session.execute(text("SELECT 1"))
                result.scalar_one()
            logger.debug("database_connection_verified")
            return True
        except Exception as e:
            logger.exception("database_connection_failed", error=str(e))
            return False

    async def health_check(self) -> dict:
        start = time.monotonic()
        ok = await self.verify_connection()
        elapsed = (time.monotonic() - start) * 1000
        return {
            "status": "healthy" if ok else "unhealthy",
            "response_ms": round(elapsed, 1),
            "pool_size": self._pool_size(),
            "checked_in": self._pool_checkedin(),
            "overflow": self._pool_overflow(),
        }

    def _pool_size(self) -> int | None:
        pool = self.engine.pool
        if hasattr(pool, "size"):
            return pool.size()  # type: ignore[union-attr]
        return None

    def _pool_checkedin(self) -> int | None:
        pool = self.engine.pool
        if hasattr(pool, "checkedin"):
            return pool.checkedin()  # type: ignore[union-attr]
        return None

    def _pool_overflow(self) -> int | None:
        pool = self.engine.pool
        if hasattr(pool, "overflow"):
            return pool.overflow()  # type: ignore[union-attr]
        return None

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        async with self.session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        async with self.session_factory() as session:
            yield session

    def _safe_url(self) -> str:
        url = str(self.engine.url)
        if "@" in url:
            parts = url.split("@")
            return f"***@{parts[-1]}"
        return url


def _default_json_serializer(obj: object) -> str:
    import json

    return json.dumps(obj, default=str, ensure_ascii=False)


def get_db(settings: Settings) -> Database:
    return Database(settings)
