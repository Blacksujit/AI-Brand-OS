from __future__ import annotations

import uuid

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from core.logging import get_logger
from models.knowledge import KnowledgeEntry, KnowledgeTag

logger = get_logger(__name__)


class KnowledgeEntryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, entry: KnowledgeEntry) -> KnowledgeEntry:
        self._session.add(entry)
        await self._session.flush()
        return entry

    async def get_by_id(self, entry_id: uuid.UUID) -> KnowledgeEntry | None:
        result = await self._session.execute(
            select(KnowledgeEntry).where(KnowledgeEntry.id == entry_id)
        )
        return result.scalar_one_or_none()

    async def list_by_user(
        self,
        user_id: uuid.UUID,
        offset: int = 0,
        limit: int = 20,
        tag: str | None = None,
        source_type: str | None = None,
    ) -> list[KnowledgeEntry]:
        query = select(KnowledgeEntry).where(KnowledgeEntry.user_id == user_id)
        if tag:
            query = query.join(KnowledgeTag).where(KnowledgeTag.name == tag)
        if source_type:
            query = query.where(KnowledgeEntry.source_type == source_type)
        query = query.order_by(KnowledgeEntry.created_at.desc()).offset(offset).limit(limit)
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def count_by_user(
        self,
        user_id: uuid.UUID,
        tag: str | None = None,
        source_type: str | None = None,
    ) -> int:
        query = select(func.count(KnowledgeEntry.id)).where(KnowledgeEntry.user_id == user_id)
        if tag:
            query = query.join(KnowledgeTag).where(KnowledgeTag.name == tag)
        if source_type:
            query = query.where(KnowledgeEntry.source_type == source_type)
        result = await self._session.execute(query)
        return result.scalar_one()

    async def update_entry(
        self,
        entry_id: uuid.UUID,
        values: dict,
    ) -> KnowledgeEntry | None:
        await self._session.execute(
            update(KnowledgeEntry).where(KnowledgeEntry.id == entry_id).values(**values)
        )
        return await self.get_by_id(entry_id)

    async def delete_entry(self, entry_id: uuid.UUID) -> None:
        await self._session.execute(delete(KnowledgeEntry).where(KnowledgeEntry.id == entry_id))

    async def search_keyword(
        self,
        user_id: uuid.UUID,
        query_text: str,
        limit: int = 10,
        offset: int = 0,
    ) -> list[KnowledgeEntry]:
        stmt = (
            select(KnowledgeEntry)
            .where(KnowledgeEntry.user_id == user_id)
            .where(
                KnowledgeEntry.title.ilike(f"%{query_text}%")
                | KnowledgeEntry.content.ilike(f"%{query_text}%")
                | KnowledgeEntry.summary.ilike(f"%{query_text}%")
            )
            .order_by(KnowledgeEntry.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def count_keyword(
        self,
        user_id: uuid.UUID,
        query_text: str,
    ) -> int:
        stmt = (
            select(func.count(KnowledgeEntry.id))
            .where(KnowledgeEntry.user_id == user_id)
            .where(
                KnowledgeEntry.title.ilike(f"%{query_text}%")
                | KnowledgeEntry.content.ilike(f"%{query_text}%")
                | KnowledgeEntry.summary.ilike(f"%{query_text}%")
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def get_recent(self, user_id: uuid.UUID, limit: int = 20) -> list[KnowledgeEntry]:
        result = await self._session.execute(
            select(KnowledgeEntry)
            .where(KnowledgeEntry.user_id == user_id)
            .order_by(KnowledgeEntry.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())


class KnowledgeTagRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add_tag(self, tag: KnowledgeTag) -> KnowledgeTag:
        self._session.add(tag)
        await self._session.flush()
        return tag

    async def remove_tag(self, tag_id: uuid.UUID) -> None:
        await self._session.execute(delete(KnowledgeTag).where(KnowledgeTag.id == tag_id))

    async def get_tags_for_entry(self, entry_id: uuid.UUID) -> list[KnowledgeTag]:
        result = await self._session.execute(
            select(KnowledgeTag).where(KnowledgeTag.entry_id == entry_id)
        )
        return list(result.scalars().all())

    async def get_tags_by_name(self, entry_id: uuid.UUID, name: str) -> KnowledgeTag | None:
        result = await self._session.execute(
            select(KnowledgeTag).where(KnowledgeTag.entry_id == entry_id, KnowledgeTag.name == name)
        )
        return result.scalar_one_or_none()

    async def get_distinct_tags(self, user_id: uuid.UUID) -> list[tuple[str, int]]:
        result = await self._session.execute(
            select(KnowledgeTag.name, func.count(KnowledgeTag.id))
            .join(KnowledgeEntry)
            .where(KnowledgeEntry.user_id == user_id)
            .group_by(KnowledgeTag.name)
            .order_by(func.count(KnowledgeTag.id).desc())
        )
        return [(row[0], row[1]) for row in result.all()]

    async def set_tags(self, entry_id: uuid.UUID, tag_names: list[str]) -> list[KnowledgeTag]:
        existing = await self.get_tags_for_entry(entry_id)
        existing_names = {t.name for t in existing}
        for tag_obj in existing:
            if tag_obj.name not in tag_names:
                await self.remove_tag(tag_obj.id)
        for name in tag_names:
            if name not in existing_names:
                tag = KnowledgeTag(entry_id=entry_id, name=name)
                self._session.add(tag)
        return await self.get_tags_for_entry(entry_id)
