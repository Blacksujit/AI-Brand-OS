from __future__ import annotations

from httpx import AsyncClient, ASGITransport
import pytest
import pytest_asyncio

from app.core.config import Settings
from app.core.db import Database, Base
from app.main import app


@pytest_asyncio.fixture
async def test_settings() -> Settings:
    return Settings(
        env="test",
        debug=False,
        database_url="sqlite+aiosqlite://",
        redis_url="redis://localhost:6379/1",
        jwt_secret="test-secret-that-is-at-least-32-characters!!",
        encryption_key="test-encryption-key-32-bytes-long!!",
    )


def override_get_settings() -> Settings:
    return Settings(
        env="test",
        debug=False,
        database_url="sqlite+aiosqlite://",
        redis_url="redis://localhost:6379/1",
        jwt_secret="test-secret-that-is-at-least-32-characters!!",
        encryption_key="test-encryption-key-32-bytes-long!!",
    )


@pytest.mark.asyncio
async def test_register_user() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "password": "securepassword123",
                "display_name": "Test User",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data


@pytest.mark.asyncio
async def test_register_duplicate_email() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "dupe@example.com",
                "password": "securepassword123",
                "display_name": "User One",
            },
        )
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "dupe@example.com",
                "password": "securepassword123",
                "display_name": "User Two",
            },
        )
        assert response.status_code == 409


@pytest.mark.asyncio
async def test_login_invalid_credentials() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "wrongpassword",
            },
        )
        assert response.status_code == 401


@pytest.mark.asyncio
async def test_health() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
