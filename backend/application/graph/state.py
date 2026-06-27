from __future__ import annotations

from typing import TypedDict


class ContentState(TypedDict):
    user_id: str
    session_id: str
    pipeline_id: str
    topic: str | None
    platform: str
    tone: str
    max_length: int

    current_step: str
    errors: list[str]
    requires_human_approval: bool

    research_output: dict | None
    knowledge_output: dict | None
    memory_output: dict | None
    topic_output: dict | None
    strategy_output: dict | None
    hooks_output: dict | None
    draft_output: dict | None
    review_output: dict | None
    analytics_output: dict | None

    final_output: dict | None

    step_timing: dict[str, float]
