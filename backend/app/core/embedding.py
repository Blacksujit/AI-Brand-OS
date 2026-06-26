from __future__ import annotations

from typing import Any

from app.core.cache import CacheService


class EmbeddingService:
    def __init__(self, llm_client: Any, cache: CacheService) -> None:
        self._llm = llm_client
        self._cache = cache

    async def embed_text(self, text: str, model: str = "default") -> list[float]:
        cache_key = f"emb:{hash(text)}"
        cached = await self._cache.get(cache_key)
        if cached is not None:
            return cached
        response = await self._llm.embed(text)
        if not response.embeddings:
            raise ValueError("Embedding returned empty result")
        vector = response.embeddings[0]
        await self._cache.set(cache_key, vector, ttl=86400)
        return vector

    async def embed_texts(
        self, texts: list[str], model: str = "default"
    ) -> list[list[float]]:
        uncached: list[tuple[int, str]] = []
        results: list[list[float] | None] = [None] * len(texts)
        for i, text in enumerate(texts):
            cached = await self._cache.get(f"emb:{hash(text)}")
            if cached is not None:
                results[i] = cached
            else:
                uncached.append((i, text))
        if uncached:
            indices = [i for i, _ in uncached]
            texts_to_embed = [t for _, t in uncached]
            response = await self._llm.embed(texts_to_embed)
            for idx, vec in zip(indices, response.embeddings, strict=False):
                results[idx] = vec
                await self._cache.set(
                    f"emb:{hash(texts_to_embed[indices.index(idx)])}",
                    vec,
                    ttl=86400,
                )
        return [r for r in results if r is not None]

    async def cosine_similarity(
        self, a: list[float], b: list[float]
    ) -> float:
        import math
        dot = sum(x * y for x, y in zip(a, b, strict=True))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(x * x for x in b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)
