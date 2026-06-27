from __future__ import annotations

from pydantic import BaseModel, Field


class AddKnowledgeEntryRequest(BaseModel):
    title: str = Field(min_length=1, max_length=512)
    content: str = Field(min_length=1)
    source_type: str = Field(default="other", max_length=64)
    source_id: str = Field(default="", max_length=256)
    summary: str | None = None
    tags: list[str] = []


class UpdateKnowledgeEntryRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=512)
    content: str | None = None
    summary: str | None = None
    source_type: str | None = Field(default=None, max_length=64)
    source_id: str | None = Field(default=None, max_length=256)
    tags: list[str] | None = None


class KnowledgeEntryResponse(BaseModel):
    id: str
    user_id: str
    source_type: str
    source_id: str
    title: str
    content: str
    summary: str | None = None
    tags: list[str] = []
    created_at: str
    updated_at: str | None = None


class KnowledgeEntryListItem(BaseModel):
    id: str
    title: str
    summary: str | None = None
    source_type: str
    tags: list[str] = []
    created_at: str
    relevance_score: float | None = None


class KnowledgeSearchResult(BaseModel):
    item: KnowledgeEntryListItem
    score: float
    match_type: str = "hybrid"


class KnowledgeSearchResponse(BaseModel):
    results: list[KnowledgeSearchResult]
    total: int


class KnowledgeListResponse(BaseModel):
    items: list[KnowledgeEntryListItem]
    total: int
    page: int
    page_size: int
    has_more: bool


class KnowledgeTagResponse(BaseModel):
    name: str
    count: int


class IngestUrlRequest(BaseModel):
    url: str = Field(min_length=1)
    title: str | None = None
    tags: list[str] = []


class IngestMarkdownRequest(BaseModel):
    title: str = Field(min_length=1, max_length=512)
    content: str = Field(min_length=1)
    source_id: str | None = None
    tags: list[str] = []


class IngestResponse(BaseModel):
    entry_id: str
    title: str
    summary: str | None = None
    tags: list[str] = []
    processing_duration_ms: int


class KnowledgeContextResponse(BaseModel):
    items: list[KnowledgeEntryListItem]
    tags: list[KnowledgeTagResponse]
    total_count: int
