from __future__ import annotations

from typing import Any

import chromadb
from chromadb.api import Collection

from core.config import Settings
from core.logging import get_logger

logger = get_logger(__name__)


class ChromaService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client: chromadb.AsyncClientAPI | None = None
        self._collections: dict[str, Collection] = {}

    async def initialize(self) -> bool:
        try:
            self._client = await chromadb.AsyncHttpClient(
                host=self._settings.chromadb_host,
                port=self._settings.chromadb_port,
            )
            await self._client.heartbeat()
            self._collections["kb"] = await self._get_or_create_collection(
                self._settings.chromadb_collection_kb,
            )
            logger.info("chroma_initialized", collections=list(self._collections.keys()))
            return True
        except Exception as exc:
            logger.warning("chroma_init_failed", error=str(exc))
            self._client = None
            return False

    async def close(self) -> None:
        if self._client:
            await self._client.heartbeat()
        logger.info("chroma_closed")

    async def _get_or_create_collection(self, name: str) -> Any:
        if self._client is None:
            msg = "ChromaDB not initialized"
            raise RuntimeError(msg)
        try:
            return await self._client.get_collection(name)
        except Exception:
            return await self._client.create_collection(
                name=name,
                metadata={
                    "hnsw:space": "cosine",
                    "hnsw:M": 16,
                    "hnsw:ef_construction": 100,
                },
            )

    async def upsert_embedding(
        self,
        collection_name: str,
        entry_id: str,
        embedding: list[float],
        metadata: dict[str, Any],
        document: str | None = None,
    ) -> None:
        if self._client is None:
            msg = "ChromaDB not initialized"
            raise RuntimeError(msg)
        collection = await self._ensure_collection(collection_name)
        await collection.upsert(
            ids=[entry_id],
            embeddings=[embedding],
            metadatas=[metadata],
            documents=[document] if document else None,
        )

    async def delete_embedding(
        self,
        collection_name: str,
        entry_id: str,
    ) -> None:
        if self._client is None:
            msg = "ChromaDB not initialized"
            raise RuntimeError(msg)
        collection = await self._ensure_collection(collection_name)
        try:
            await collection.delete(ids=[entry_id])
        except Exception:
            logger.warning("chroma_delete_not_found", entry_id=entry_id)

    async def query_embeddings(
        self,
        collection_name: str,
        query_embedding: list[float],
        n_results: int = 10,
        where: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if self._client is None:
            msg = "ChromaDB not initialized"
            raise RuntimeError(msg)
        collection = await self._ensure_collection(collection_name)
        return await collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where,
        )

    async def count_entries(self, collection_name: str) -> int:
        if self._client is None:
            msg = "ChromaDB not initialized"
            raise RuntimeError(msg)
        collection = await self._ensure_collection(collection_name)
        return await collection.count()

    async def health_check(self) -> dict[str, Any]:
        if self._client is None:
            return {"status": "not_initialized"}
        try:
            await self._client.heartbeat()
            count = await self.count_entries("kb")
            return {"status": "healthy", "kb_entries": count}
        except Exception as exc:
            return {"status": "unhealthy", "error": str(exc)}

    async def _ensure_collection(self, name: str) -> Any:
        if name not in self._collections:
            self._collections[name] = await self._get_or_create_collection(name)
        return self._collections[name]
