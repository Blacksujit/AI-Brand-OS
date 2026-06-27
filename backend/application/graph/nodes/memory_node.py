from __future__ import annotations

import time
from typing import Any


def make_memory_node():
    async def memory_node(state: ContentState) -> dict:
        start = time.monotonic()
        result = {
            "session_count": 1,
            "previous_topics": [],
            "insights": [],
            "latency_ms": int((time.monotonic() - start) * 1000),
        }
        return {"memory_output": result, "current_step": "memory"}

    return memory_node


_memory_node = make_memory_node()
memory_node = _memory_node
