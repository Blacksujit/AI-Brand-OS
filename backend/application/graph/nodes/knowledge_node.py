from __future__ import annotations

import time
from typing import Any

from application.graph.state import ContentState


def make_knowledge_node(kb_service: Any | None = None):
    async def knowledge_node(state: ContentState) -> dict:
        start = time.monotonic()
        tags: list[str] = []
        recent_items: list[dict[str, Any]] = []
        search_results: list[dict[str, Any]] = []

        if kb_service:
            try:
                tag_objs = await kb_service.get_tags(state["user_id"])
                tags = [t.name if hasattr(t, "name") else str(t) for t in (tag_objs or [])]
            except Exception:
                tags = []

            topic = state.get("research_output", {}).get("dominant_theme") or state.get("topic") or ""

            try:
                query_text = topic or ""
                if query_text:
                    search_resp = await kb_service.search(state["user_id"], query_text, limit=5)
                    search_results = [
                        {
                            "id": str(r.item.id) if hasattr(r.item, "id") else r.item.get("id", ""),
                            "title": r.item.title if hasattr(r.item, "title") else r.item.get("title", ""),
                            "summary": r.item.summary if hasattr(r.item, "summary") else r.item.get("summary", ""),
                            "source_type": r.item.source_type if hasattr(r.item, "source_type") else r.item.get("source_type", ""),
                            "score": r.score,
                            "match_type": r.match_type,
                        }
                        for r in search_resp.results
                    ]

                items = await kb_service.get_recent_context(state["user_id"], limit=5)
                recent_items = [
                    {
                        "id": str(getattr(i, "id", "")),
                        "title": str(getattr(i, "title", "")),
                        "summary": str(getattr(i, "summary", "")),
                        "source_type": str(getattr(i, "source_type", "")),
                    }
                    for i in (items or [])
                ]
            except Exception:
                search_results = []
                recent_items = []

        result = {
            "recent_tags": tags,
            "search_results": search_results,
            "recent_items": recent_items,
            "total_items": len(search_results) + len(recent_items),
            "latency_ms": int((time.monotonic() - start) * 1000),
        }
        return {"knowledge_output": result, "current_step": "knowledge"}

    return knowledge_node
