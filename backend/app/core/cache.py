from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Any

import redis.asyncio as aioredis

from app.core.config import Settings


class CacheService:
    def __init__(self, settings: Settings) -> None:
        self._client: aioredis.Redis | None = None
        self._settings = settings

    async def initialize(self) -> None:
        self._client = await aioredis.from_url(
            self._settings.redis_url,
            decode_responses=True,
            max_connections=20,
        )

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()

    async def get(self, key: str) -> Any | None:
        if not self._client:
            return None
        value = await self._client.get(key)
        if value is None:
            return None
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return value

    async def set(
        self, key: str, value: Any, ttl: int | None = None
    ) -> None:
        if not self._client:
            return
        encoded = json.dumps(value, default=str)
        if ttl is not None:
            await self._client.setex(key, ttl, encoded)
        else:
            await self._client.set(key, encoded)

    async def delete(self, key: str) -> bool:
        if not self._client:
            return False
        return bool(await self._client.delete(key))

    async def exists(self, key: str) -> bool:
        if not self._client:
            return False
        return bool(await self._client.exists(key))

    async def expire(self, key: str, ttl: int) -> bool:
        if not self._client:
            return False
        return bool(await self._client.expire(key, ttl))

    async def ttl(self, key: str) -> int:
        if not self._client:
            return -2
        return await self._client.ttl(key)

    async def incr(self, key: str, amount: int = 1) -> int:
        if not self._client:
            return 0
        return await self._client.incr(key, amount)

    async def keys(self, pattern: str) -> list[str]:
        if not self._client:
            return []
        return [k async for k in self._client.scan_iter(match=pattern)]

    async def get_or_set(
        self, key: str, factory, ttl: int | None = None
    ) -> Any:
        cached = await self.get(key)
        if cached is not None:
            return cached
        value = await factory()
        await self.set(key, value, ttl)
        return value

    async def pipeline_get(self, keys: list[str]) -> dict[str, Any]:
        if not self._client or not keys:
            return {}
        values = await self._client.mget(*keys)
        result: dict[str, Any] = {}
        for key, value in zip(keys, values, strict=False):
            if value is not None:
                try:
                    result[key] = json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    result[key] = value
        return result


def get_cache(settings: Settings) -> CacheService:
    return CacheService(settings)
