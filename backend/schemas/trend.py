from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class TrendSignalBase(BaseModel):
    source_type: str = Field(max_length=32)
    source_id: str = Field(max_length=256)
    source_url: str | None = None
    title: str = Field(max_length=512)
    summary: str | None = None
    raw_content: str | None = None
    keywords: list[str] | None = None
    entities: list[str] | None = None
    categories: list[str] | None = None
    relevance_score: float = 0.0
    extra_data: dict | None = None


class TrendSignalCreate(TrendSignalBase):
    pass


class TrendSignalResponse(TrendSignalBase):
    id: UUID
    created_at: datetime
    updated_at: datetime | None = None
    embedding: list[float] | None = None

    class Config:
        from_attributes = True


class TrendTopicResponse(BaseModel):
    id: UUID
    name: str
    description: str | None = None
    signal_count: int
    velocity: float
    peak_score: float
    status: str
    representative_signals: list[str] | None = None
    keywords: list[str] | None = None
    centroid_embedding: list[float] | None = None
    created_at: datetime
    updated_at: datetime | None = None

    class Config:
        from_attributes = True


class TrendTopicCreate(BaseModel):
    name: str = Field(max_length=256)
    description: str | None = None
    keywords: list[str] | None = None


class TrendTopicUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=256)
    description: str | None = None
    status: str | None = Field(default=None, max_length=32)
    velocity: float | None = None
    keywords: list[str] | None = None


class TrendAnalysisCreate(BaseModel):
    topic_ids: list[UUID] = Field(min_length=1)
    generated_for: str | None = Field(default=None, max_length=256)


class TrendAnalysisResponse(BaseModel):
    id: UUID
    user_id: UUID
    topic_ids: list[str]
    insights: str
    recommendations: list[str] | None = None
    confidence: float
    generated_for: str | None = None
    extra_data: dict | None = None
    created_at: datetime
    updated_at: datetime | None = None

    class Config:
        from_attributes = True


class TrendSignalIngestRequest(BaseModel):
    signals: list[TrendSignalCreate] = Field(min_length=1, max_length=100)


class TrendSignalIngestResponse(BaseModel):
    created: int
    updated: int
    skipped: int


class TrendClusteringRequest(BaseModel):
    min_signals_per_topic: int = Field(default=3, ge=2, le=20)
    similarity_threshold: float = Field(default=0.7, ge=0.3, le=0.95)
    max_topics: int = Field(default=50, ge=1, le=200)
    time_window_days: int = Field(default=7, ge=1, le=90)


class TrendClusteringResponse(BaseModel):
    topics_created: int
    topics_updated: int
    signals_clustered: int


class TrendScoreRequest(BaseModel):
    topic_ids: list[UUID] | None = None
    recency_weight: float = Field(default=0.5, ge=0.0, le=1.0)
    velocity_weight: float = Field(default=0.3, ge=0.0, le=1.0)
    relevance_weight: float = Field(default=0.2, ge=0.0, le=1.0)


class TrendSearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=256)
    limit: int = Field(default=20, ge=1, le=100)
    source_type: str | None = Field(default=None, max_length=32)
    min_relevance: float = Field(default=0.0, ge=0.0, le=1.0)


class TrendTopicListResponse(BaseModel):
    topics: list[TrendTopicResponse]
    total: int
    page: int
    page_size: int


class TrendSignalListResponse(BaseModel):
    signals: list[TrendSignalResponse]
    total: int
    page: int
    page_size: int
