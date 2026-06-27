from __future__ import annotations

import time
from typing import Any


def make_knowledge_node(kb_service: Any | None = None):
    async def knowledge_node(state: ContentState) -> dict:
        start = time.monotonic()
        tags: list[str] = []
        recent_items: list[dict[str, Any]] = []

        if kb_service:
            try:
                tag_objs = await kb_service.get_tags(state["user_id"])
                tags = [t.name if hasattr(t, "name") else str(t) for t in (tag_objs or [])]
            except Exception:
                tags = []

            try:
                items = await kb_service.get_recent_context(state["user_id"], limit=10)
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
                recent_items = []

        result = {
            "recent_tags": tags,
            "recent_items": recent_items,
            "total_items": len(recent_items),
            "latency_ms": int((time.monotonic() - start) * 1000),
        }
        return {"knowledge_output": result, "current_step": "knowledge"}

    return knowledge_node
