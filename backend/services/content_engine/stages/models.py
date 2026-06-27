from __future__ import annotations

import uuid
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, Field


class ContentCategory(StrEnum):
    TUTORIAL = "tutorial"
    OPINION = "opinion"
    PROJECT_UPDATE = "project_update"
    PAPER_SUMMARY = "paper_summary"
    INDUSTRY_ANALYSIS = "industry_analysis"
    PERSONAL_STORY = "personal_story"
    CODE_DEEP_DIVE = "code_deep_dive"


class SignalBreakdown(BaseModel):
    has_github_activity: bool = False
    has_kb_recent: bool = False
    has_trends: bool = False
    dominant_signal: Literal["github", "knowledge", "trends", "mixed"] = "mixed"
    signal_quality: float = 0.0


class SignalWeights(BaseModel):
    github_recency: float = 0.35
    github_volume: float = 0.15
    kb_freshness: float = 0.25
    kb_diversity: float = 0.10
    trend_relevance: float = 0.10
    trend_freshness: float = 0.05


class AggregatedContext(BaseModel):
    user_id: uuid.UUID
    recent_github_topics: list[str] = []
    recent_kb_tags: list[str] = []
    trending_topics: list[str] = []
    expertise_areas: list[str] = []
    aggregated_summary: str = ""
    signal_breakdown: SignalBreakdown = Field(default_factory=SignalBreakdown)


class ContentIdea(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    title: str
    description: str
    angle: str
    category: ContentCategory = ContentCategory.OPINION
    relevance_score: float = 0.5
    novelty_score: float = 0.5
    source_signals: list[str] = []
    suggested_tone: Literal["educational", "opinion", "insight", "tutorial", "story"] = "opinion"
    suggested_length: Literal["short", "medium", "long"] = "medium"
    reasoning: str = ""


class NoveltyScore(BaseModel):
    is_novel: bool = True
    similarity_to_past_posts: float = 0.0
    duplicate_of_recent_brief: bool = False
    similar_existing_ideas: list[str] = []


class CompositionParams(BaseModel):
    tone: Literal["conversational", "professional", "technical", "inspirational"] = "conversational"
    length: Literal["short", "medium", "long"] = "medium"
    platform: str = "linkedin"
    include_code: bool = False
    include_personal_anecdote: bool = True
    target_audience: Literal["peers", "managers", "general_tech", "founders"] = "peers"
    creativity_level: float = 0.7


class CompositionResult(BaseModel):
    draft_id: uuid.UUID
    title: str
    body: str
    hook: str = ""
    call_to_action: str = ""
    hashtags: list[str] = []
    word_count: int = 0
    reading_time_seconds: int = 0
    llm_used: str = ""
    tokens_used: int = 0
    composition_duration_ms: int = 0
    has_code_blocks: bool = False
    sections: list[str] = []


class RefinementResult(BaseModel):
    original_body: str
    refined_body: str
    changes_applied: list[StyleChange] = []
    style_adherence_score: float = 0.0


class StyleChange(BaseModel):
    change_type: str
    original: str
    refined: str
    reason: str


class QualityDimensions(BaseModel):
    factual_accuracy: float = 0.0
    hallucination_risk: float = 0.0
    readability: float = 0.0
    authenticity: float = 0.0
    technical_depth: float = 0.0
    engagement_potential: float = 0.0
    platform_appropriateness: float = 0.0


class QualityWarning(BaseModel):
    severity: Literal["critical", "major", "minor"] = "minor"
    category: str = ""
    message: str = ""
    affected_text: str | None = None
    suggestion: str | None = None


class QualityVerdict(BaseModel):
    overall_score: float = 0.0
    verdict: Literal["pass", "warn", "fail"] = "fail"
    dimensions: QualityDimensions = Field(default_factory=QualityDimensions)
    warnings: list[QualityWarning] = []
    recommendations: list[str] = []


class SectionQuality(BaseModel):
    section: str
    score: float
    issues: list[str] = []


class StageContext(BaseModel):
    """Mutable context that flows through the 5 pipeline stages."""

    user_id: uuid.UUID
    aggregated_context: AggregatedContext | None = None
    ideas: list[ContentIdea] = []
    selected_idea: ContentIdea | None = None
    composition: CompositionResult | None = None
    refinement: RefinementResult | None = None
    quality: QualityVerdict | None = None
    params: CompositionParams = Field(default_factory=CompositionParams)
    metadata: dict[str, Any] = {}
