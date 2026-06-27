from __future__ import annotations

import uuid
from typing import Any

from core.chroma import ChromaService
from core.embedding import EmbeddingService
from core.logging import get_logger
from database.db import Database
from models.knowledge import KnowledgeEntry, KnowledgeTag
from repositories.knowledge import KnowledgeEntryRepository, KnowledgeTagRepository
from schemas.knowledge import (
    AddKnowledgeEntryRequest,
    KnowledgeEntryListItem,
    KnowledgeListResponse,
    KnowledgeSearchResponse,
    KnowledgeSearchResult,
    KnowledgeTagResponse,
    UpdateKnowledgeEntryRequest,
)

logger = get_logger(__name__)


class KnowledgeBaseService:
    def __init__(
        self,
        db: Database,
        chroma: ChromaService,
        embedding: EmbeddingService,
    ) -> None:
        self._db = db
        self._chroma = chroma
        self._embedding = embedding

    async def add_entry(
        self,
        user_id: uuid.UUID,
        request: AddKnowledgeEntryRequest,
    ) -> KnowledgeEntry:
        async with self._db.session() as session:
            repo = KnowledgeEntryRepository(session)
            tag_repo = KnowledgeTagRepository(session)

            entry = KnowledgeEntry(
                user_id=user_id,
                source_type=request.source_type,
                source_id=request.source_id or "",
                title=request.title,
                content=request.content,
                summary=request.summary,
            )
            entry = await repo.create(entry)

            if request.tags:
                for tag_name in request.tags:
                    tag = KnowledgeTag(entry_id=entry.id, name=tag_name)
                    await tag_repo.add_tag(tag)

        await self._embed_and_store(user_id, entry)
        return entry

    async def get_entry(self, user_id: uuid.UUID, entry_id: uuid.UUID) -> KnowledgeEntry | None:
        async with self._db.session() as session:
            repo = KnowledgeEntryRepository(session)
            entry = await repo.get_by_id(entry_id)
            if entry and entry.user_id != user_id:
                return None
            return entry

    async def update_entry(
        self,
        user_id: uuid.UUID,
        entry_id: uuid.UUID,
        request: UpdateKnowledgeEntryRequest,
    ) -> KnowledgeEntry | None:
        async with self._db.session() as session:
            repo = KnowledgeEntryRepository(session)
            tag_repo = KnowledgeTagRepository(session)

            entry = await repo.get_by_id(entry_id)
            if not entry or entry.user_id != user_id:
                return None

            update_values: dict[str, Any] = {}
            for field in ("title", "content", "summary", "source_type", "source_id"):
                val = getattr(request, field, None)
                if val is not None:
                    update_values[field] = val

            entry = await repo.update_entry(entry_id, update_values)

            if request.tags is not None:
                await tag_repo.set_tags(entry_id, request.tags)

        if update_values.get("title") or update_values.get("content"):
            entry = await self.get_entry(user_id, entry_id)
            if entry:
                await self._embed_and_store(user_id, entry)

        return entry

    async def delete_entry(self, user_id: uuid.UUID, entry_id: uuid.UUID) -> bool:
        async with self._db.session() as session:
            repo = KnowledgeEntryRepository(session)
            entry = await repo.get_by_id(entry_id)
            if not entry or entry.user_id != user_id:
                return False
            await repo.delete_entry(entry_id)

        if self._chroma._client is not None:
            await self._chroma.delete_embedding("kb", str(entry_id))
        return True

    async def list_entries(
        self,
        user_id: uuid.UUID,
        page: int = 1,
        page_size: int = 20,
        tag: str | None = None,
        source_type: str | None = None,
    ) -> KnowledgeListResponse:
        offset = (page - 1) * page_size
        async with self._db.session() as session:
            repo = KnowledgeEntryRepository(session)
            items = await repo.list_by_user(
                user_id=user_id,
                offset=offset,
                limit=page_size,
                tag=tag,
                source_type=source_type,
            )
            total = await repo.count_by_user(
                user_id=user_id,
                tag=tag,
                source_type=source_type,
            )
        return KnowledgeListResponse(
            items=[self._to_list_item(e) for e in items],
            total=total,
            page=page,
            page_size=page_size,
            has_more=(offset + page_size) < total,
        )

    async def search(
        self,
        user_id: uuid.UUID,
        query_text: str,
        limit: int = 10,
    ) -> KnowledgeSearchResponse:
        results: list[KnowledgeSearchResult] = []

        if self._chroma._client is not None:
            query_embedding = await self._embedding.embed_text(query_text)
            try:
                chroma_results = await self._chroma.query_embeddings(
                    "kb",
                    query_embedding,
                    n_results=limit,
                    where={"user_id": str(user_id)},
                )
            except RuntimeError:
                chroma_results = {}

            chroma_ids: list[str] = (
                chroma_results.get("ids", [[]])[0] if chroma_results.get("ids") else []
            )
            chroma_distances: list[float] = (
                chroma_results.get("distances", [[]])[0] if chroma_results.get("distances") else []
            )

            async with self._db.session() as session:
                repo = KnowledgeEntryRepository(session)
                for cid, dist in zip(chroma_ids, chroma_distances, strict=True):
                    entry_id = cid.replace("kb_", "")
                    try:
                        entry = await repo.get_by_id(uuid.UUID(entry_id))
                    except Exception:
                        continue
                    if entry and entry.user_id == user_id:
                        score = 1.0 - dist if dist <= 1.0 else 0.0
                        results.append(
                            KnowledgeSearchResult(
                                item=self._to_list_item(entry),
                                score=round(score, 4),
                                match_type="semantic",
                            )
                        )

        if not results:
            async with self._db.session() as session:
                repo = KnowledgeEntryRepository(session)
                keyword_items = await repo.search_keyword(
                    user_id=user_id, query_text=query_text, limit=limit
                )
                results = [
                    KnowledgeSearchResult(
                        item=self._to_list_item(e),
                        score=0.5,
                        match_type="keyword",
                    )
                    for e in keyword_items
                ]

        return KnowledgeSearchResponse(results=results, total=len(results))

    async def get_tags(self, user_id: uuid.UUID) -> list[KnowledgeTagResponse]:
        async with self._db.session() as session:
            tag_repo = KnowledgeTagRepository(session)
            tags = await tag_repo.get_distinct_tags(user_id)
        return [KnowledgeTagResponse(name=t, count=c) for t, c in tags]

    async def get_recent_context(
        self, user_id: uuid.UUID, limit: int = 20
    ) -> list[KnowledgeEntryListItem]:
        async with self._db.session() as session:
            repo = KnowledgeEntryRepository(session)
            items = await repo.get_recent(user_id, limit)
        return [self._to_list_item(e) for e in items]

    async def _embed_and_store(
        self,
        user_id: uuid.UUID,
        entry: KnowledgeEntry,
    ) -> None:
        if self._chroma._client is None:
            logger.warning("chroma_unavailable_skipping_embed", entry_id=str(entry.id))
            return
        text = f"{entry.title}\n\n{entry.summary or ''}\n\n{entry.content}"
        embedding = await self._embedding.embed_text(text[:2000])
        async with self._db.session() as session:
            tag_repo = KnowledgeTagRepository(session)
            tags = await tag_repo.get_tags_for_entry(entry.id)
        tag_names = [t.name for t in tags]
        chroma_id = f"kb_{entry.id}"
        await self._chroma.upsert_embedding(
            "kb",
            chroma_id,
            embedding,
            metadata={
                "knowledge_entry_id": str(entry.id),
                "user_id": str(user_id),
                "source_type": entry.source_type,
                "title": entry.title,
                "tags": tag_names,
                "saved_at": entry.created_at.isoformat(),
                "model_version": self._embedding.dimension,
            },
            document=text[:1000],
        )

    def _to_list_item(self, entry: KnowledgeEntry) -> KnowledgeEntryListItem:
        return KnowledgeEntryListItem(
            id=str(entry.id),
            title=entry.title,
            summary=entry.summary,
            source_type=entry.source_type,
            tags=[],
            created_at=entry.created_at.isoformat(),
            relevance_score=entry.relevance_score,
        )
