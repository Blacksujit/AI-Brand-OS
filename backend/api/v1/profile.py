from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status

from api.deps import (
    get_current_user_id,
    get_db_session,
    require_onboarded,
)
from database import Database
from schemas.profile import (
    OnboardingRequest,
    ProfileResponse,
    ProfileUpdate,
)
from services.profile import ProfileService

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("/me", response_model=ProfileResponse)
async def get_my_profile(
    user_id: uuid.UUID = Depends(require_onboarded),
    db: Database = Depends(get_db_session),
) -> ProfileResponse:
    service = ProfileService(db)
    profile = await service.get_profile(user_id)
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found",
        )
    return ProfileResponse(**profile)  # type: ignore[arg-type]


@router.patch("/me", response_model=ProfileResponse)
async def update_my_profile(
    body: ProfileUpdate,
    user_id: uuid.UUID = Depends(require_onboarded),
    db: Database = Depends(get_db_session),
) -> ProfileResponse:
    service = ProfileService(db)
    updates = body.model_dump(exclude_none=True)
    result = await service.update_profile(user_id, updates)
    return ProfileResponse(**result)  # type: ignore[arg-type]


@router.post("/onboarding", response_model=ProfileResponse)
async def complete_onboarding(
    body: OnboardingRequest,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: Database = Depends(get_db_session),
) -> ProfileResponse:
    service = ProfileService(db)
    result = await service.onboard_user(user_id, body.model_dump())
    return ProfileResponse(**result)  # type: ignore[arg-type]
