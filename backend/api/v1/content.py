# ruff: noqa: B008
from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status

from api.deps import get_current_user_id, get_history_service, get_knowledge_service, get_trend_service, get_security_service
from core.config import get_settings
from core.llm import LLMClient
from core.logging import get_logger
from core.security import SecurityService
from schemas.content import (
    EvaluateContentRequest,
    EvaluateContentResponse,
    GeneratedPostResponse,
    HistoryListResponse,
    IdeaResponse,
    IdeasRequest,
    PipelineGenerateRequest,
    PipelineOutputResponse,
    PipelineStatusResponse,
)
from services.content_engine.service import ContentEngine
from services.evaluation import EvaluationService
from services.history import HistoryService
from services.knowledge import KnowledgeBaseService
from services.research import ResearchService

router = APIRouter(prefix="/content", tags=["content"])
logger = get_logger(__name__)

_content_graph = None


def _get_content_graph(kb_service: KnowledgeBaseService | None = None, trend_service: Any | None = None):
    global _content_graph
    if _content_graph is None:
        from application.graph.graph import build_content_graph
        from services.prompt.service import PromptService
        from core.llm import LLMClient
        from core.config import get_settings
        from services.research import ResearchService  # IMPORT

        settings = get_settings()
        
        # Create and WIRE ResearchService with TrendService
        research_service = ResearchService()
        research_service.wire(trend_service)  # WIRE IT!

        _content_graph = build_content_graph(
            llm=LLMClient(settings),
            prompt_service=PromptService(),
            research_service=research_service,  # PASS WIRED SERVICE
            kb_service=kb_service,
            langsmith_api_key=settings.langchain_api_key,
            langsmith_project=settings.langchain_project,
        )
        logger.info("content_graph_built")
    return _content_graph


def _record_to_response(record: Any) -> GeneratedPostResponse:
    return GeneratedPostResponse(
        id=str(record.id),
        title=record.title,
        body=record.body,
        hook=record.hook or None,
        call_to_action=record.call_to_action or None,
        hashtags=list(record.hashtags) if record.hashtags else [],
        quality_score=record.quality_score,
        review_feedback=record.review_feedback,
        status=record.status,
        platform=record.platform,
        created_at=record.created_at.isoformat(),
    )


@router.post("/generate", response_model=PipelineStatusResponse)
async def generate_content(
    request: PipelineGenerateRequest,
    user_id: uuid.UUID = Depends(get_current_user_id),
    history: HistoryService = Depends(get_history_service),
    kb: KnowledgeBaseService = Depends(get_knowledge_service),
    trend: Any = Depends(get_trend_service),  # WIRE TREND SERVICE
) -> dict[str, Any]:
    import time as time_module

    graph = _get_content_graph(kb_service=kb, trend_service=trend)
    start = time_module.time()

    pipeline_id = str(request.pipeline_id or uuid.uuid4())

    result = await graph.ainvoke(
        {
            "user_id": str(user_id),
            "session_id": str(request.session_id or uuid.uuid4()),
            "pipeline_id": pipeline_id,
            "topic": request.topic,
            "platform": request.platform,
            "tone": request.tone or "professional",
            "max_length": request.max_length or 280,
            "current_step": "",
            "errors": [],
            "requires_human_approval": False,
            "research_output": None,
            "knowledge_output": None,
            "memory_output": None,
            "topic_output": None,
            "strategy_output": None,
            "hooks_output": None,
            "draft_output": None,
            "review_output": None,
            "analytics_output": None,
            "final_output": None,
            "step_timing": {},
        }
    )

    draft_output = result.get("draft_output") or {}
    review_output = result.get("review_output") or {}
    strategy_output = result.get("strategy_output") or {}
    draft = draft_output.get("draft", {})
    topic = strategy_output.get("topic") or request.topic or "Untitled"

    if draft and draft.get("body"):
        await history.record_generation(
            user_id=user_id,
            title=topic,
            body=draft.get("body", ""),
            platform=request.platform,
            quality_score=review_output.get("score"),
            review_feedback=review_output.get("feedback"),
            hook=draft.get("hook", ""),
            call_to_action=draft.get("call_to_action", ""),
            hashtags=draft.get("hashtags", []),
            duration_ms=int((time_module.time() - start) * 1000),
        )

    await history.store_pipeline_state(pipeline_id, result)

    requires_approval = result.get("requires_human_approval", False)
    errors = result.get("errors", [])

    return {
        "pipeline_id": result.get("pipeline_id", ""),
        "is_complete": result.get("current_step") in ("analytics", "review")
        or not requires_approval,
        "current_step": result.get("current_step", ""),
        "steps_completed": [
            k for k in ("research", "knowledge", "memory", "topic_selection", "strategy", "hook_generation", "writing", "review", "analytics")
            if result.get(f"{k}_output") is not None
        ],
        "errors": [{"step": e, "error": "See pipeline output"} for e in errors] if errors else [],
        "duration_ms": int((time_module.time() - start) * 1000),
        "requires_human_approval": requires_approval,
    }


@router.get("/pipeline/{pipeline_id}", response_model=PipelineStatusResponse)
async def get_pipeline_status(
    pipeline_id: str,
    user_id: uuid.UUID = Depends(get_current_user_id),
    history: HistoryService = Depends(get_history_service),
) -> dict[str, Any]:
    state = history.get_pipeline_state(pipeline_id)
    if state is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pipeline not found")
    requires_approval = state.get("requires_human_approval", False)
    errors = state.get("errors", [])
    return {
        "pipeline_id": pipeline_id,
        "is_complete": state.get("current_step") in ("analytics", "review") or not requires_approval,
        "current_step": state.get("current_step", ""),
        "steps_completed": [
            k for k in ("research", "knowledge", "memory", "topic_selection", "strategy", "hook_generation", "writing", "review", "analytics")
            if state.get(f"{k}_output") is not None
        ],
        "errors": [{"step": e, "error": "See pipeline output"} for e in errors] if errors else [],
        "duration_ms": state.get("step_timing", {}).get("total_ms", 0),
        "requires_human_approval": requires_approval,
    }


@router.get("/pipeline/{pipeline_id}/output", response_model=PipelineOutputResponse)
async def get_pipeline_output(
    pipeline_id: str,
    user_id: uuid.UUID = Depends(get_current_user_id),
    history: HistoryService = Depends(get_history_service),
) -> dict[str, Any]:
    state = history.get_pipeline_state(pipeline_id)
    if state is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pipeline not found")
    draft_output = state.get("draft_output") or {}
    review_output = state.get("review_output") or {}
    errors = state.get("errors", [])
    return {
        "pipeline_id": pipeline_id,
        "pipeline_type": "content_generation",
        "total_duration_ms": state.get("step_timing", {}).get("total_ms", 0),
        "steps_completed": len([
            k for k in ("research", "knowledge", "memory", "topic_selection", "strategy", "hook_generation", "writing", "review", "analytics")
            if state.get(f"{k}_output") is not None
        ]),
        "errors": len(errors),
        "requires_human_approval": state.get("requires_human_approval", False),
        "draft": draft_output.get("draft", {}),
        "review": review_output,
        "strategy": state.get("strategy_output", {}).get("strategy", {}),
        "topic": state.get("topic", ""),
    }


@router.post("/ideas", response_model=list[IdeaResponse])
async def generate_ideas(
    request: IdeasRequest,
    user_id: uuid.UUID = Depends(get_current_user_id),
    kb: KnowledgeBaseService = Depends(get_knowledge_service),
    trend: Any = Depends(get_trend_service),
) -> list[dict[str, Any]]:
    settings = get_settings()
    content_engine = ContentEngine(
        llm=LLMClient(settings),
        kb_service=kb,
        trend_service=trend,
    )
    ideas = await content_engine.generate_ideas(
        user_id=user_id,
        count=request.count,
        expertise_areas=request.expertise_areas or [],
    )
    return [
        {
            "id": str(uuid.uuid4()),
            "title": idea.title,
            "description": idea.description,
            "relevance_score": idea.relevance_score,
            "platform": request.platform,
        }
        for idea in ideas
    ]


@router.post("/evaluate", response_model=EvaluateContentResponse)
async def evaluate_content(
    request: EvaluateContentRequest,
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> dict[str, Any]:
    evaluator = EvaluationService()
    metrics = await evaluator.evaluate_text(
        text=request.body,
        title=request.title,
    )
    score = metrics.overall_score
    if score >= 0.7:
        verdict = "excellent"
    elif score >= 0.5:
        verdict = "good"
    elif score >= 0.3:
        verdict = "fair"
    else:
        verdict = "poor"
    return {
        "score": score,
        "verdict": verdict,
        "feedback": " ".join(metrics.feedback) if metrics.feedback else "Content looks good",
        "issues": metrics.feedback,
        "strengths": [] if score < 0.5 else ["Coherent structure", "Appropriate length"],
    }


@router.get("/history", response_model=HistoryListResponse)
async def list_history(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    platform: str | None = Query(default=None, max_length=32),
    status: str | None = Query(default=None, max_length=16),
    user_id: uuid.UUID = Depends(get_current_user_id),
    history: HistoryService = Depends(get_history_service),
) -> dict[str, Any]:
    records = history.get_history(
        user_id=user_id,
        limit=page_size,
        offset=(page - 1) * page_size,
        platform=platform,
        status=status,
    )
    return {
        "records": [_record_to_response(r) for r in records],
        "total": len(records),
        "page": page,
        "page_size": page_size,
    }


@router.get("/history/{record_id}", response_model=GeneratedPostResponse)
async def get_history_record(
    record_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    history: HistoryService = Depends(get_history_service),
) -> GeneratedPostResponse:
    record = history.get_record(user_id, record_id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Record not found")
    return _record_to_response(record)


@router.patch("/history/{record_id}/status", response_model=GeneratedPostResponse)
async def update_record_status(
    record_id: uuid.UUID,
    status: str = Query(pattern="^(draft|published|archived)$"),
    user_id: uuid.UUID = Depends(get_current_user_id),
    history: HistoryService = Depends(get_history_service),
) -> GeneratedPostResponse:
    record = history.update_status(
        user_id=user_id,
        record_id=record_id,
        status=status,  # type: ignore[arg-type]
    )
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Record not found")
    return _record_to_response(record)
