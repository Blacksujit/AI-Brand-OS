from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends

from api.deps import get_current_user_id, get_style_service
from schemas.style import (
    AnalyzeTextRequest,
    ImportContentRequest,
    ImportContentResponse,
    RateDraftRequest,
    StyleAnalysisResponse,
    StyleInsightsResponse,
    StyleProfileResponse,
    StyleProfileUpdate,
)
from services.style.service import StyleService

router = APIRouter(prefix="/style", tags=["style"])


@router.get("/profile", response_model=StyleProfileResponse)
async def get_profile(
    user_id: UUID = Depends(get_current_user_id),
    service: StyleService = Depends(get_style_service),
) -> StyleProfileResponse:
    profile = await service.get_profile(user_id)
    return profile


@router.put("/profile", response_model=StyleProfileResponse)
async def update_profile(
    body: StyleProfileUpdate,
    user_id: UUID = Depends(get_current_user_id),
    service: StyleService = Depends(get_style_service),
) -> StyleProfileResponse:
    updates = {}
    if body.learning_rate is not None:
        updates["learning_rate"] = body.learning_rate
    if body.style_params is not None:
        updates["style_params"] = body.style_params.model_dump()
    profile = await service.update_profile(user_id, updates)
    return profile


@router.post("/analyze", response_model=StyleAnalysisResponse)
async def analyze_text(
    body: AnalyzeTextRequest,
    user_id: UUID = Depends(get_current_user_id),
    service: StyleService = Depends(get_style_service),
) -> dict:
    result = await service.analyze(user_id, body.text)
    return result


@router.post("/import", response_model=ImportContentResponse)
async def import_content(
    body: ImportContentRequest,
    user_id: UUID = Depends(get_current_user_id),
    service: StyleService = Depends(get_style_service),
) -> dict:
    texts = body.posts
    if body.source_labels:
        texts = [
            f"{label}\n\n{post}" for label, post in zip(body.source_labels, texts, strict=False)
        ]
    result = await service.import_content(user_id, texts)
    return result


@router.post("/rate", response_model=StyleProfileResponse)
async def rate_draft(
    body: RateDraftRequest,
    user_id: UUID = Depends(get_current_user_id),
    service: StyleService = Depends(get_style_service),
) -> StyleProfileResponse:
    ds = body.dimension_scores.model_dump() if body.dimension_scores else None
    profile = await service.rate_draft(
        user_id,
        body.draft_id,
        body.score,
        body.comment,
        ds,
    )
    return profile


@router.get("/insights", response_model=StyleInsightsResponse)
async def get_insights(
    user_id: UUID = Depends(get_current_user_id),
    service: StyleService = Depends(get_style_service),
) -> dict:
    result = await service.get_insights(user_id)
    return result


@router.get("/progress")
async def get_progress(
    user_id: UUID = Depends(get_current_user_id),
    service: StyleService = Depends(get_style_service),
) -> dict:
    result = await service.get_learning_progress(user_id)
    return result
