from __future__ import annotations

from collections.abc import AsyncGenerator
from pathlib import Path
from typing import Any

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.cache import CacheService
from app.core.config import Settings
from app.core.db import Base, Database
from app.core.security import SecurityService


@pytest.fixture
def settings() -> Settings:
    return Settings(
        env="test",
        debug=False,
        database_url="sqlite+aiosqlite://",
        redis_url="redis://localhost:6379/1",
        jwt_secret="test-secret-that-is-at-least-32-characters!!",
        encryption_key="test-encryption-key-32-bytes-long!!",
        data_dir=Path("/tmp/brandos-test"),
    )


@pytest_asyncio.fixture
async def db(settings: Settings) -> AsyncGenerator[Database, None]:
    engine = create_async_engine(
        settings.database_url,
        echo=False,
        connect_args={"check_same_thread": False},
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    database = Database.__new__(Database)
    database.engine = engine
    database.session_factory = session_factory
    database._data_dir = settings.data_dir

    try:
        yield database
    finally:
        await engine.dispose()


@pytest_asyncio.fixture
async def session(db: Database) -> AsyncGenerator[AsyncSession, None]:
    async with db.session_factory() as s:
        yield s
        await s.rollback()


@pytest.fixture
def security(settings: Settings) -> SecurityService:
    return SecurityService(settings)


@pytest.fixture
def token(security: SecurityService, test_user_id: Any) -> str:
    return security.create_access_token(test_user_id)
