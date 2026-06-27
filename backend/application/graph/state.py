from __future__ import annotations

from typing import Optional, TypedDict


class ContentState(TypedDict):
    user_id: str
    session_id: str
    pipeline_id: str
    topic: Optional[str]
    platform: str
    tone: str
    max_length: int

    current_step: str
    errors: list[str]
    requires_human_approval: bool

    research_output: Optional[dict]
    knowledge_output: Optional[dict]
    memory_output: Optional[dict]
    topic_output: Optional[dict]
    strategy_output: Optional[dict]
    hooks_output: Optional[dict]
    draft_output: Optional[dict]
    review_output: Optional[dict]
    analytics_output: Optional[dict]

    final_output: Optional[dict]

    step_timing: dict[str, float]
