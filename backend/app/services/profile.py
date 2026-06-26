from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import CacheService
from app.core.db import Database
from app.core.logging import get_logger
from app.models.profile import Profile
from app.models.user import User

logger = get_logger(__name__)


class ProfileService:
    def __init__(self, db: Database, cache: CacheService) -> None:
        self._db = db
        self._cache = cache

    async def get_profile(self, user_id: uuid.UUID) -> dict[str, Any] | None:
        cache_key = f"profile:{user_id}"
        cached = await self._cache.get(cache_key)
        if cached is not None:
            return cached

        async with self._db.session() as session:
            result = await session.execute(
                select(Profile).where(Profile.user_id == user_id)
            )
            profile = result.scalar_one_or_none()
            if profile is None:
                return None

            user_result = await session.execute(
                select(User).where(User.id == user_id)
            )
            user = user_result.scalar_one_or_none()
            if user is None:
                return None

            data = {
                "id": str(profile.id),
                "user_id": str(profile.user_id),
                "display_name": user.display_name,
                "email": user.email,
                "avatar_url": user.avatar_url,
                "bio": profile.bio,
                "website": profile.website,
                "location": profile.location,
                "preferences": profile.preferences or {},
                "created_at": profile.created_at.isoformat(),
                "updated_at": profile.updated_at.isoformat()
                if profile.updated_at
                else None,
            }

            await self._cache.set(cache_key, data, ttl=300)
            return data

    async def update_profile(
        self, user_id: uuid.UUID, updates: dict[str, Any]
    ) -> dict[str, Any]:
        async with self._db.session() as session:
            result = await session.execute(
                select(Profile).where(Profile.user_id == user_id)
            )
            profile = result.scalar_one_or_none()
            if profile is None:
                profile = Profile(user_id=user_id)
                session.add(profile)

            allowed_fields = {"bio", "website", "location", "preferences"}
            for field, value in updates.items():
                if field in allowed_fields and hasattr(profile, field):
                    setattr(profile, field, value)

            if "display_name" in updates:
                user_result = await session.execute(
                    select(User).where(User.id == user_id)
                )
                user = user_result.scalar_one_or_none()
                if user:
                    user.display_name = updates["display_name"]

            await session.flush()
            await self._cache.delete(f"profile:{user_id}")
            return await self.get_profile(user_id)  # type: ignore[return-value]

    async def onboard_user(
        self, user_id: uuid.UUID, onboarding_data: dict[str, Any]
    ) -> dict[str, Any]:
        async with self._db.session() as session:
            user_result = await session.execute(
                select(User).where(User.id == user_id)
            )
            user = user_result.scalar_one_or_none()
            if user is None:
                raise ValueError("User not found")

            result = await session.execute(
                select(Profile).where(Profile.user_id == user_id)
            )
            profile = result.scalar_one_or_none()
            if profile is None:
                profile = Profile(user_id=user_id)
                session.add(profile)

            profile.bio = onboarding_data.get("bio")
            profile.website = onboarding_data.get("website")
            profile.location = onboarding_data.get("location")
            profile.preferences = onboarding_data.get("preferences", {})

            user.is_onboarded = True
            if "display_name" in onboarding_data:
                user.display_name = onboarding_data["display_name"]

            await self._cache.delete(f"profile:{user_id}")
            return await self.get_profile(user_id)  # type: ignore[return-value]
