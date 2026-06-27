from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class GenerationRequest(BaseModel):
    topic: str = Field(min_length=1, max_length=500)
    platform: str = Field(default="linkedin", max_length=32)
    tone: str = Field(default="professional", max_length=32)
    max_length: int = Field(default=300, ge=50, le=3000)


class PipelineGenerateRequest(BaseModel):
    topic: str | None = Field(default=None, max_length=500)
    platform: str = Field(default="linkedin", max_length=32)
    tone: str = Field(default="professional", max_length=32)
    max_length: int = Field(default=300, ge=50, le=3000)
    pipeline_type: Literal["daily_brief", "draft_generation", "analytics"] = "draft_generation"


class PipelineStatusResponse(BaseModel):
    pipeline_id: str
    is_complete: bool
    current_step: str
    steps_completed: list[str]
    errors: list[dict[str, Any]]
    duration_ms: int
    requires_human_approval: bool = False


class GeneratedPostResponse(BaseModel):
    id: str
    title: str
    body: str
    hook: str | None = None
    call_to_action: str | None = None
    hashtags: list[str] = []
    quality_score: float | None = None
    review_feedback: str | None = None
    status: str = "draft"
    platform: str = "linkedin"
    created_at: str
    published_at: str | None = None


class ReviewResponse(BaseModel):
    verdict: str
    score: float
    feedback: str
    issues: list[str] = []


class IdeasRequest(BaseModel):
    topic: str | None = Field(default=None, max_length=500)
    platform: str = Field(default="linkedin", max_length=32)
    count: int = Field(default=5, ge=1, le=20)


class IdeaResponse(BaseModel):
    id: str
    title: str
    description: str
    relevance_score: float = 0.0
    platform: str = "linkedin"


class EvaluateContentRequest(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    body: str = Field(min_length=1, max_length=10000)
    platform: str = Field(default="linkedin", max_length=32)


class EvaluateContentResponse(BaseModel):
    score: float
    verdict: str
    feedback: str
    issues: list[str]
    strengths: list[str]


class PipelineOutputResponse(BaseModel):
    pipeline_id: str
    pipeline_type: str
    total_duration_ms: int
    steps_completed: int
    errors: int
    requires_human_approval: bool
    draft: dict[str, Any] = {}
    review: dict[str, Any] = {}
    strategy: dict[str, Any] = {}
    topic: str = ""


class HistoryListResponse(BaseModel):
    records: list[GeneratedPostResponse]
    total: int
    page: int
    page_size: int
