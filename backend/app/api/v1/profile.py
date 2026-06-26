from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.api.deps import (
    get_cache_session,
    get_current_user_id,
    require_onboarded,
)
from app.core.cache import CacheService
from app.core.db import Database
from app.services.profile import ProfileService

router = APIRouter(prefix="/profile", tags=["profile"])


class ProfileResponse(BaseModel):
    id: str
    user_id: str
    display_name: str
    email: str
    avatar_url: str | None = None
    bio: str | None = None
    website: str | None = None
    location: str | None = None
    preferences: dict[str, Any] = {}
    created_at: str
    updated_at: str | None = None


class ProfileUpdate(BaseModel):
    display_name: str | None = Field(None, max_length=128)
    bio: str | None = None
    website: str | None = None
    location: str | None = None
    preferences: dict[str, Any] | None = None


class OnboardingRequest(BaseModel):
    display_name: str = Field(min_length=1, max_length=128)
    bio: str | None = None
    website: str | None = None
    location: str | None = None
    preferences: dict[str, Any] = {}


@router.get("/me", response_model=ProfileResponse)
async def get_my_profile(
    user_id: uuid.UUID = Depends(require_onboarded),
    db: Database = Depends(get_cache_session),
    cache: CacheService = Depends(get_cache_session),
) -> dict:
    service = ProfileService(db, cache)
    profile = await service.get_profile(user_id)
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found",
        )
    return profile


@router.patch("/me", response_model=ProfileResponse)
async def update_my_profile(
    body: ProfileUpdate,
    user_id: uuid.UUID = Depends(require_onboarded),
    db: Database = Depends(get_cache_session),
    cache: CacheService = Depends(get_cache_session),
) -> dict:
    service = ProfileService(db, cache)
    updates = body.model_dump(exclude_none=True)
    return await service.update_profile(user_id, updates)


@router.post("/onboarding", response_model=ProfileResponse)
async def complete_onboarding(
    body: OnboardingRequest,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: Database = Depends(get_cache_session),
    cache: CacheService = Depends(get_cache_session),
) -> dict:
    service = ProfileService(db, cache)
    return await service.onboard_user(
        user_id, body.model_dump()
    )
