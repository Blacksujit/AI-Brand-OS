from __future__ import annotations

import json
import time
from typing import Any

from application.graph.state import ContentState
from core.llm import ChatMessage, CompletionRequest, LLMClient
from core.logging import get_logger
from services.prompt.service import PromptService

logger = get_logger(__name__)


def make_strategy_node(llm: LLMClient | None = None, prompt_service: PromptService | None = None):
    async def strategy_node(state: ContentState) -> dict:
        start = time.monotonic()
        topic_output = state.topic_output or {}
        memory = state.memory_output or {}
        topic = topic_output.get("topic", state.topic or "")
        state_errors = list(state.errors)

        if llm and prompt_service:
            try:
                strategy = await _llm_strategy(topic, state, llm, prompt_service)
            except Exception as exc:
                state_errors.append({"step": "strategy", "message": str(exc)})
                logger.warning("strategy_node_llm_failed", error=str(exc))
                strategy = _default_strategy(topic)
        else:
            strategy = _default_strategy(topic)

        latency_ms = int((time.monotonic() - start) * 1000)
        result: dict[str, Any] = {
            "topic": topic,
            "strategy": strategy,
            "latency_ms": latency_ms,
        }
        return {
            "strategy_output": result,
            "current_step": "strategy",
            "errors": state_errors,
            "step_timing": {**state.step_timing, "strategy": latency_ms},
        }

    return strategy_node


async def _llm_strategy(
    topic: str, state: ContentState, llm: LLMClient, prompt_service: PromptService
) -> dict[str, Any]:
    system_prompt, user_prompt = prompt_service.build_prompt(
        "strategy_agent",
        system_vars={"topic": topic},
        user_vars={
            "topic": topic,
            "platform": state.platform,
            "tone": state.tone,
        },
    )
    request = CompletionRequest(
        model="gemini-2.0-flash",
        messages=[ChatMessage(role="user", content=user_prompt)],
        system_prompt=system_prompt,
        temperature=0.7,
        max_tokens=1024,
        response_format="json_object",
    )
    response = await llm.complete(request)
    return json.loads(response.content)


def _default_strategy(topic: str) -> dict[str, Any]:
    return {
        "angle": f"A practical perspective on {topic}",
        "tone": "conversational",
        "key_points": [
            f"Start with a personal observation about {topic}",
            "Share a specific example or data point",
            "End with a actionable takeaway",
        ],
        "structure": ["hook", "context", "insight", "takeaway", "cta"],
        "target_audience": "peers",
        "content_type": "opinion",
    }
