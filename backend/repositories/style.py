from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy import update as sql_update
from sqlalchemy.ext.asyncio import AsyncSession

from models.style import StyleProfile, StyleRating, StyleSignal


class StyleProfileRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_user_id(self, user_id: uuid.UUID) -> StyleProfile | None:
        result = await self._session.execute(
            select(StyleProfile).where(StyleProfile.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def create(self, profile: StyleProfile) -> StyleProfile:
        self._session.add(profile)
        await self._session.flush()
        return profile

    async def update(self, profile_id: uuid.UUID, values: dict) -> StyleProfile | None:
        result = await self._session.execute(
            sql_update(StyleProfile)
            .where(StyleProfile.id == profile_id)
            .values(**values)
            .returning(StyleProfile)
        )
        return result.scalar_one_or_none()

    async def upsert_by_user_id(self, user_id: uuid.UUID, defaults: dict) -> StyleProfile:
        existing = await self.get_by_user_id(user_id)
        if existing:
            await self._session.execute(
                sql_update(StyleProfile).where(StyleProfile.id == existing.id).values(**defaults)
            )
            for key, val in defaults.items():
                setattr(existing, key, val)
            return existing
        profile = StyleProfile(user_id=user_id, **defaults)
        self._session.add(profile)
        await self._session.flush()
        return profile


class StyleSignalRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, signal: StyleSignal) -> StyleSignal:
        self._session.add(signal)
        await self._session.flush()
        return signal

    async def count_by_profile(
        self,
        profile_id: uuid.UUID,
        signal_type: str | None = None,
    ) -> int:
        stmt = select(StyleSignal).where(StyleSignal.profile_id == profile_id)
        if signal_type:
            stmt = stmt.where(StyleSignal.signal_type == signal_type)
        result = await self._session.execute(stmt)
        return len(result.scalars().all())

    async def list_recent(
        self,
        profile_id: uuid.UUID,
        limit: int = 50,
    ) -> list[StyleSignal]:
        result = await self._session.execute(
            select(StyleSignal)
            .where(StyleSignal.profile_id == profile_id)
            .order_by(StyleSignal.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())


class StyleRatingRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, rating: StyleRating) -> StyleRating:
        self._session.add(rating)
        await self._session.flush()
        return rating

    async def get_by_user_and_draft(
        self,
        user_id: uuid.UUID,
        draft_id: str,
    ) -> StyleRating | None:
        result = await self._session.execute(
            select(StyleRating).where(
                StyleRating.user_id == user_id,
                StyleRating.draft_id == draft_id,
            )
        )
        return result.scalar_one_or_none()

    async def count_by_user(self, user_id: uuid.UUID) -> int:
        result = await self._session.execute(
            select(StyleRating).where(StyleRating.user_id == user_id)
        )
        return len(result.scalars().all())

    async def list_recent(self, user_id: uuid.UUID, limit: int = 20) -> list[StyleRating]:
        result = await self._session.execute(
            select(StyleRating)
            .where(StyleRating.user_id == user_id)
            .order_by(StyleRating.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
