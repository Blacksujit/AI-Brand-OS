from __future__ import annotations

import time
from typing import Any

from application.graph.state import ContentState


def make_topic_selection_node():
    async def topic_selection_node(state: ContentState) -> dict:
        start = time.monotonic()
        research = state.research_output or {}
        knowledge = state.knowledge_output or {}

        findings = research.get("findings", [])
        tags = knowledge.get("recent_tags", [])
        dominant_theme = research.get("dominant_theme", "")

        candidates: list[dict[str, Any]] = []
        seen_titles: set[str] = set()

        for f in findings:
            title = f.get("title", "Untitled")
            if title.lower() in seen_titles:
                continue
            seen_titles.add(title.lower())
            candidates.append(
                {
                    "title": title,
                    "description": f.get("description", ""),
                    "source": f.get("source", "trend"),
                    "relevance_score": f.get("relevance_score", 0.5),
                }
            )

        if tags and not candidates:
            for tag in tags[:5]:
                candidates.append(
                    {
                        "title": f"Explain {tag}",
                        "description": f"A deep dive into {tag} based on recent knowledge",
                        "source": "knowledge_base",
                        "relevance_score": 0.6,
                    }
                )

        candidates.sort(key=lambda c: c.get("relevance_score", 0), reverse=True)
        selected = candidates[0] if candidates else {"title": state.topic or "General update"}

        selected_title = selected.get("title", "")
        topic = state.topic or selected_title
        latency_ms = int((time.monotonic() - start) * 1000)
        result = {
            "topic": topic,
            "selected_candidate": selected,
            "candidates": candidates[:5],
            "total_candidates": len(candidates),
            "latency_ms": latency_ms,
        }
        return {
            "topic_output": result,
            "current_step": "topic_selection",
            "errors": list(state.errors),
            "step_timing": {**state.step_timing, "topic_selection": latency_ms},
        }

    return topic_selection_node
