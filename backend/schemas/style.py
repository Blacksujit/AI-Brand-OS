from __future__ import annotations

from pydantic import BaseModel, Field


class StyleParams(BaseModel):
    preferred_terms: list[str] = []
    avoided_terms: list[str] = []
    avg_sentence_length: float = 20.0
    avg_paragraph_length: float = 3.0
    formality: float = 0.5
    humor_frequency: float = 0.3
    analogy_frequency: float = 0.3
    technical_depth: float = 0.5
    citation_preference: float = 0.3
    code_example_frequency: float = 0.2
    sentence_variety: float = 0.5
    passive_voice_frequency: float = 0.3


class StyleProfileResponse(BaseModel):
    id: str
    user_id: str
    style_params: StyleParams
    learning_rate: float
    confidence: float
    total_ratings: int
    total_edits: int
    total_approved: int
    is_stable: bool


class StyleProfileUpdate(BaseModel):
    learning_rate: float | None = Field(default=None, ge=0.01, le=0.5)
    style_params: StyleParams | None = None


class RatingDimensions(BaseModel):
    authenticity: int = Field(default=3, ge=1, le=5)
    technical_depth: int = Field(default=3, ge=1, le=5)
    readability: int = Field(default=3, ge=1, le=5)
    relevance: int = Field(default=3, ge=1, le=5)
    tone: int = Field(default=3, ge=1, le=5)


class RateDraftRequest(BaseModel):
    draft_id: str = Field(min_length=1, max_length=36)
    score: int = Field(ge=1, le=5)
    comment: str | None = None
    dimension_scores: RatingDimensions | None = None


class ImportContentRequest(BaseModel):
    posts: list[str] = Field(min_length=1, max_length=50)
    source_labels: list[str] | None = None


class ImportContentResponse(BaseModel):
    signals_created: int
    profile_confidence: float


class AnalyzeTextRequest(BaseModel):
    text: str = Field(min_length=50, max_length=50000)


class StyleAnalysisResponse(BaseModel):
    vocabulary_match: float
    sentence_structure_match: float
    tone_alignment: float
    technical_depth_match: float
    overall_similarity: float
    deviations: list[str] = []


class LearningProgressResponse(BaseModel):
    signals_collected: int
    signals_needed_for_stable: int = 50
    profile_confidence: float
    is_stable: bool
    days_until_stable_estimate: int | None = None


class StyleInsightItem(BaseModel):
    dimension: str
    value: float
    trend: str = "stable"


class StyleInsightsResponse(BaseModel):
    dominant_characteristics: list[str] = []
    top_improvement_areas: list[str] = []
    consistency_trend: str = "stable"
    insights: list[StyleInsightItem] = []
