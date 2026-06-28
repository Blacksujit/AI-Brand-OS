from __future__ import annotations

from pydantic import BaseModel, Field


class ContentState(BaseModel):
    user_id: str
    session_id: str
    pipeline_id: str
    topic: str | None = None
    platform: str = "linkedin"
    tone: str = "professional"
    max_length: int = 280

    current_step: str = ""
    errors: list[dict] = Field(default_factory=list)
    requires_human_approval: bool = False

    research_output: dict | None = None
    knowledge_output: dict | None = None
    memory_output: dict | None = None
    topic_output: dict | None = None
    strategy_output: dict | None = None
    hooks_output: dict | None = None
    draft_output: dict | None = None
    review_output: dict | None = None
    analytics_output: dict | None = None

    final_output: dict | None = None

    revision_count: int = 0
    step_timing: dict[str, float] = Field(default_factory=dict)
