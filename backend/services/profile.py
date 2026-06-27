from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select

from core.logging import get_logger
from database.db import Database
from models.profile import Profile
from models.user import User

logger = get_logger(__name__)


class ProfileService:
    def __init__(self, db: Database) -> None:
        self._db = db

    async def get_profile(self, user_id: uuid.UUID) -> dict[str, Any] | None:
        async with self._db.session() as session:
            result = await session.execute(select(Profile).where(Profile.user_id == user_id))
            profile = result.scalar_one_or_none()
            if profile is None:
                return None

            user_result = await session.execute(select(User).where(User.id == user_id))
            user = user_result.scalar_one_or_none()
            if user is None:
                return None

            return {
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
                "updated_at": profile.updated_at.isoformat() if profile.updated_at else None,
            }

    async def update_profile(self, user_id: uuid.UUID, updates: dict[str, Any]) -> dict[str, Any]:
        async with self._db.session() as session:
            result = await session.execute(select(Profile).where(Profile.user_id == user_id))
            profile = result.scalar_one_or_none()
            if profile is None:
                profile = Profile(user_id=user_id)
                session.add(profile)

            allowed_fields = {"bio", "website", "location", "preferences"}
            for field, value in updates.items():
                if field in allowed_fields and hasattr(profile, field):
                    setattr(profile, field, value)

            user: User | None = None
            if "display_name" in updates:
                user_result = await session.execute(select(User).where(User.id == user_id))
                user = user_result.scalar_one_or_none()
                if user:
                    user.display_name = updates["display_name"]

            await session.flush()
            await session.refresh(profile)

            if user is None:
                user_result = await session.execute(select(User).where(User.id == user_id))
                user = user_result.scalar_one_or_none()

            return {
                "id": str(profile.id),
                "user_id": str(profile.user_id),
                "display_name": user.display_name if user else "",
                "email": user.email if user else "",
                "avatar_url": user.avatar_url if user else None,
                "bio": profile.bio,
                "website": profile.website,
                "location": profile.location,
                "preferences": profile.preferences or {},
                "created_at": profile.created_at.isoformat(),
                "updated_at": profile.updated_at.isoformat() if profile.updated_at else None,
            }

    async def onboard_user(
        self, user_id: uuid.UUID, onboarding_data: dict[str, Any]
    ) -> dict[str, Any]:
        async with self._db.session() as session:
            user_result = await session.execute(select(User).where(User.id == user_id))
            user = user_result.scalar_one_or_none()
            if user is None:
                msg = "User not found"
                raise ValueError(msg)

            result = await session.execute(select(Profile).where(Profile.user_id == user_id))
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

            await session.flush()
            await session.refresh(profile)

            return {
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
                "updated_at": profile.updated_at.isoformat() if profile.updated_at else None,
            }
