from __future__ import annotations

import time
from collections import Counter
from typing import Any

from application.graph.state import ContentState
from core.logging import get_logger
from services.research import ResearchService

logger = get_logger(__name__)


def make_research_node(research_service: ResearchService | None = None):
    async def research_node(state: ContentState) -> dict:
        start = time.monotonic()
        expertise: list[str] = []
        findings: list[dict[str, Any]] = []
        state_errors = list(state.errors)

        if research_service:
            try:
                raw = await research_service.get_context_for_agent(
                    state.user_id, expertise or None
                )
                findings = raw
            except Exception as exc:
                state_errors.append({"step": "research", "message": str(exc)})
                logger.warning("research_node_failed", error=str(exc))
                findings = []

        latency_ms = int((time.monotonic() - start) * 1000)
        result = {
            "findings": findings,
            "total_findings": len(findings),
            "sources_queried": 1 if findings else 0,
            "dominant_theme": _extract_theme(findings),
            "latency_ms": latency_ms,
        }
        return {
            "research_output": result,
            "current_step": "research",
            "errors": state_errors,
            "step_timing": {**state.step_timing, "research": latency_ms},
        }

    return research_node


def _extract_theme(findings: list[dict[str, Any]]) -> str | None:
    if not findings:
        return None
    keywords: list[str] = []
    for f in findings:
        title = f.get("title", "")
        desc = f.get("description", "")
        keywords.extend(title.lower().split()[:5])
        keywords.extend(desc.lower().split()[:5])
    if keywords:
        common = Counter(keywords).most_common(3)
        return " ".join(k for k, _ in common)
    return None
