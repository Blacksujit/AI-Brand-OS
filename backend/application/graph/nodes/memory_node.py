from __future__ import annotations

import time

from application.graph.state import ContentState


def make_memory_node():
    async def memory_node(state: ContentState) -> dict:
        start = time.monotonic()
        latency_ms = int((time.monotonic() - start) * 1000)
        result = {
            "session_count": 1,
            "previous_topics": [],
            "insights": [],
            "latency_ms": latency_ms,
        }
        return {
            "memory_output": result,
            "current_step": "memory",
            "errors": list(state.errors),
            "step_timing": {**state.step_timing, "memory": latency_ms},
        }

    return memory_node
