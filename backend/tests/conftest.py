from __future__ import annotations

import os
import tempfile
from collections.abc import AsyncGenerator
from pathlib import Path

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from core.config import Settings, get_settings
from database import Database, get_db

TEST_DB_DIR = Path(tempfile.gettempdir()) / "brandos_test"
TEST_DB_DIR.mkdir(parents=True, exist_ok=True)


@pytest.fixture(autouse=True)
def _test_env() -> None:
    os.environ["BRANDOS_ENV"] = "test"
    db_path = TEST_DB_DIR / f"test_{os.urandom(4).hex()}.db"
    os.environ["BRANDOS_DATABASE_URL"] = f"sqlite+aiosqlite:///{db_path}"
    os.environ["BRANDOS_LOG_LEVEL"] = "CRITICAL"
    os.environ["BRANDOS_GEMINI_API_KEY"] = "test-key"
    os.environ["BRANDOS_JWT_SECRET"] = "test-secret-that-is-long-enough-for-hs256"


@pytest.fixture(name="settings")
def fixture_settings() -> Settings:
    return get_settings()


@pytest_asyncio.fixture(name="db")
async def fixture_db(settings: Settings) -> AsyncGenerator[Database, None]:
    db = get_db(settings)
    await db.initialize()
    yield db
    await db.close()


@pytest_asyncio.fixture(name="client")
async def fixture_client(db: Database) -> AsyncGenerator[AsyncClient, None]:
    from main import app

    app.state.db = db

    transport = ASGITransport(app=app)  # type: ignore[arg-type]
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture(name="user_token")
def fixture_user_token() -> str:
    import uuid

    from core.config import get_settings
    from core.security import SecurityService

    settings = get_settings()
    security = SecurityService(settings)
    return security.create_access_token(uuid.uuid4())


@pytest.fixture(name="auth_headers")
def fixture_auth_headers(user_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {user_token}"}
