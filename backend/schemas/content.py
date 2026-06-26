from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class GenerationRequest(BaseModel):
    topic: str = Field(min_length=1, max_length=500)
    platform: str = Field(default="linkedin", max_length=32)
    tone: str = Field(default="professional", max_length=32)
    max_length: int = Field(default=300, ge=50, le=3000)


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
