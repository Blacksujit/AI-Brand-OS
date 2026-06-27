from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_endpoint(client: AsyncClient) -> None:
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] == "0.1.0"
    assert data["env"] == "test"
    assert "uptime_seconds" in data
    assert "database" in data
    assert data["database"]["status"] == "healthy"


@pytest.mark.asyncio
async def test_health_database_details(client: AsyncClient) -> None:
    response = await client.get("/health")
    data = response.json()
    db = data["database"]
    assert "response_ms" in db
    assert "pool_size" in db
    assert "checked_in" in db
    assert "overflow" in db
