from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from api.deps import get_current_user_id, get_trend_service
from schemas.trend import (
    TrendAnalysisCreate,
    TrendAnalysisResponse,
    TrendClusteringRequest,
    TrendClusteringResponse,
    TrendScoreRequest,
    TrendSearchRequest,
    TrendSignalIngestRequest,
    TrendSignalIngestResponse,
    TrendSignalListResponse,
    TrendSignalResponse,
    TrendTopicListResponse,
    TrendTopicResponse,
    TrendTopicUpdate,
)
from services.trend.service import TrendService

router = APIRouter(prefix="/trends", tags=["trends"])


@router.get("/topics", response_model=TrendTopicListResponse)
async def list_trending_topics(
    limit: int = Query(default=20, ge=1, le=100),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    service: TrendService = Depends(get_trend_service),
) -> TrendTopicListResponse:
    topics = await service.get_trending_topics(limit=limit * page)
    start = (page - 1) * page_size
    end = start + page_size
    paginated = topics[start:end]
    return TrendTopicListResponse(
        topics=[TrendTopicResponse(**t.to_dict()) for t in paginated],
        total=len(topics),
        page=page,
        page_size=page_size,
    )


@router.get("/topics/{topic_id}", response_model=TrendTopicResponse)
async def get_topic(
    topic_id: str,
    service: TrendService = Depends(get_trend_service),
) -> TrendTopicResponse:
    topic = await service.get_topic_details(topic_id)
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    return TrendTopicResponse(**topic.to_dict())


@router.patch("/topics/{topic_id}", response_model=TrendTopicResponse)
async def update_topic(
    topic_id: str,
    updates: TrendTopicUpdate,
    service: TrendService = Depends(get_trend_service),
) -> TrendTopicResponse:
    async with service._db.session() as session:
        from datetime import UTC, datetime

        from repositories.trend import TrendTopicRepository

        topic_repo = TrendTopicRepository(session)
        try:
            tid = UUID(topic_id) if isinstance(topic_id, str) else topic_id
        except (ValueError, TypeError):
            raise HTTPException(status_code=404, detail="Topic not found")
        topic = await topic_repo.get_by_id(tid)
        if not topic:
            raise HTTPException(status_code=404, detail="Topic not found")
        for key, value in updates.model_dump(exclude_none=True).items():
            setattr(topic, key, value)
        topic.updated_at = datetime.now(UTC)
        await session.commit()
        await session.refresh(topic)
    return TrendTopicResponse(**topic.to_dict())


@router.post("/signals/ingest", response_model=TrendSignalIngestResponse)
async def ingest_signals(
    request: TrendSignalIngestRequest,
    service: TrendService = Depends(get_trend_service),
) -> TrendSignalIngestResponse:
    result = await service.ingest_signals([s.model_dump() for s in request.signals])
    return TrendSignalIngestResponse(**result)


@router.get("/signals", response_model=TrendSignalListResponse)
async def list_signals(
    limit: int = Query(default=50, ge=1, le=200),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    source_type: str | None = Query(default=None, max_length=32),
    days: int = Query(default=30, ge=1, le=90),
    service: TrendService = Depends(get_trend_service),
) -> TrendSignalListResponse:
    signals = await service._get_signals_for_listing(
        limit=limit * page, source_type=source_type, days=days
    )
    start = (page - 1) * page_size
    end = start + page_size
    paginated = signals[start:end]
    return TrendSignalListResponse(
        signals=[TrendSignalResponse(**s.to_dict()) for s in paginated],
        total=len(signals),
        page=page,
        page_size=page_size,
    )


@router.post("/cluster", response_model=TrendClusteringResponse)
async def cluster_trends(
    request: TrendClusteringRequest,
    service: TrendService = Depends(get_trend_service),
) -> TrendClusteringResponse:
    result = await service.cluster_trends(
        min_signals_per_topic=request.min_signals_per_topic,
        similarity_threshold=request.similarity_threshold,
        max_topics=request.max_topics,
        time_window_days=request.time_window_days,
    )
    return TrendClusteringResponse(**result)


@router.post("/score")
async def score_trends(
    request: TrendScoreRequest,
    service: TrendService = Depends(get_trend_service),
) -> list[dict]:
    topic_ids = [str(tid) for tid in request.topic_ids] if request.topic_ids else None
    return await service.score_trends(
        topic_ids=topic_ids,
        recency_weight=request.recency_weight,
        velocity_weight=request.velocity_weight,
        relevance_weight=request.relevance_weight,
    )


@router.post("/search")
async def search_trends(
    request: TrendSearchRequest,
    service: TrendService = Depends(get_trend_service),
) -> list[TrendSignalResponse]:
    signals = await service.search_trends(
        query=request.query,
        limit=request.limit,
        source_type=request.source_type,
        min_relevance=request.min_relevance,
    )
    return [TrendSignalResponse(**s.to_dict()) for s in signals]


@router.post("/analyze", response_model=TrendAnalysisResponse)
async def generate_analysis(
    request: TrendAnalysisCreate,
    user_id: UUID = Depends(get_current_user_id),
    service: TrendService = Depends(get_trend_service),
) -> TrendAnalysisResponse:
    try:
        analysis = await service.generate_analysis(
            user_id=user_id,
            topic_ids=[str(tid) for tid in request.topic_ids],
            generated_for=request.generated_for,
        )
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
    return TrendAnalysisResponse(**analysis.to_dict())


@router.get("/analyses", response_model=list[TrendAnalysisResponse])
async def list_user_analyses(
    user_id: UUID = Depends(get_current_user_id),
    limit: int = Query(default=20, ge=1, le=100),
    service: TrendService = Depends(get_trend_service),
) -> list[TrendAnalysisResponse]:
    analyses = await service.get_user_analyses(user_id=user_id, limit=limit)
    return [TrendAnalysisResponse(**a.to_dict()) for a in analyses]
