from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.trend import TrendAnalysis, TrendSignal, TrendTopic


class TrendSignalRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, signal: TrendSignal) -> TrendSignal:
        self._session.add(signal)
        await self._session.flush()
        await self._session.refresh(signal)
        return signal

    async def get_by_id(self, signal_id: uuid.UUID) -> TrendSignal | None:
        result = await self._session.execute(select(TrendSignal).where(TrendSignal.id == signal_id))
        return result.scalar_one_or_none()

    async def get_by_source(self, source_type: str, source_id: str) -> TrendSignal | None:
        result = await self._session.execute(
            select(TrendSignal).where(
                TrendSignal.source_type == source_type,
                TrendSignal.source_id == source_id,
            )
        )
        return result.scalar_one_or_none()

    async def upsert(self, signal: TrendSignal) -> TrendSignal:
        existing = await self.get_by_source(signal.source_type, signal.source_id)
        if existing:
            for attr in [
                "source_url",
                "title",
                "summary",
                "raw_content",
                "keywords",
                "entities",
                "categories",
                "relevance_score",
                "embedding",
                "extra_data",
            ]:
                setattr(existing, attr, getattr(signal, attr))
            existing.updated_at = datetime.now(UTC)
            await self._session.flush()
            await self._session.refresh(existing)
            return existing
        return await self.add(signal)

    async def list_recent(
        self,
        limit: int = 100,
        source_type: str | None = None,
        days: int = 30,
    ) -> list[TrendSignal]:
        cutoff = datetime.now(UTC) - timedelta(days=days)
        stmt = (
            select(TrendSignal)
            .where(TrendSignal.created_at >= cutoff)
            .order_by(desc(TrendSignal.created_at))
            .limit(limit)
        )
        if source_type:
            stmt = stmt.where(TrendSignal.source_type == source_type)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def list_by_relevance(self, min_score: float = 0.5, limit: int = 50) -> list[TrendSignal]:
        result = await self._session.execute(
            select(TrendSignal)
            .where(TrendSignal.relevance_score >= min_score)
            .order_by(desc(TrendSignal.relevance_score))
            .limit(limit)
        )
        return list(result.scalars().all())

    async def count_recent(self, days: int = 30) -> int:
        cutoff = datetime.now(UTC) - timedelta(days=days)
        result = await self._session.execute(
            select(func.count(TrendSignal.id)).where(TrendSignal.created_at >= cutoff)
        )
        return result.scalar_one()


class TrendTopicRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, topic: TrendTopic) -> TrendTopic:
        self._session.add(topic)
        await self._session.flush()
        await self._session.refresh(topic)
        return topic

    async def get_by_id(self, topic_id: uuid.UUID) -> TrendTopic | None:
        result = await self._session.execute(select(TrendTopic).where(TrendTopic.id == topic_id))
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> TrendTopic | None:
        result = await self._session.execute(select(TrendTopic).where(TrendTopic.name == name))
        return result.scalar_one_or_none()

    async def list_by_status(self, status: str, limit: int = 50) -> list[TrendTopic]:
        result = await self._session.execute(
            select(TrendTopic)
            .where(TrendTopic.status == status)
            .order_by(desc(TrendTopic.velocity))
            .limit(limit)
        )
        return list(result.scalars().all())

    async def list_trending(self, limit: int = 20) -> list[TrendTopic]:
        result = await self._session.execute(
            select(TrendTopic)
            .where(TrendTopic.status.in_(["emerging", "trending", "peaking"]))
            .order_by(desc(TrendTopic.velocity))
            .limit(limit)
        )
        return list(result.scalars().all())

    async def update_velocity(self, topic_id: uuid.UUID, velocity: float) -> None:
        topic = await self.get_by_id(topic_id)
        if topic:
            topic.velocity = velocity
            topic.updated_at = datetime.now(UTC)
            await self._session.flush()

    async def update_status(self, topic_id: uuid.UUID, status: str) -> None:
        topic = await self.get_by_id(topic_id)
        if topic:
            topic.status = status
            topic.updated_at = datetime.now(UTC)
            await self._session.flush()


class TrendAnalysisRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, analysis: TrendAnalysis) -> TrendAnalysis:
        self._session.add(analysis)
        await self._session.flush()
        await self._session.refresh(analysis)
        return analysis

    async def get_by_id(self, analysis_id: uuid.UUID) -> TrendAnalysis | None:
        result = await self._session.execute(
            select(TrendAnalysis).where(TrendAnalysis.id == analysis_id)
        )
        return result.scalar_one_or_none()

    async def list_by_user(self, user_id: uuid.UUID, limit: int = 20) -> list[TrendAnalysis]:
        result = await self._session.execute(
            select(TrendAnalysis)
            .where(TrendAnalysis.user_id == user_id)
            .order_by(desc(TrendAnalysis.created_at))
            .limit(limit)
        )
        return list(result.scalars().all())

    async def count_by_user(self, user_id: uuid.UUID) -> int:
        result = await self._session.execute(
            select(func.count(TrendAnalysis.id)).where(TrendAnalysis.user_id == user_id)
        )
        return result.scalar_one()
