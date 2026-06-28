from __future__ import annotations

import json
import time
from typing import Any

from application.graph.state import ContentState
from core.llm import ChatMessage, CompletionRequest, LLMClient
from core.logging import get_logger
from services.prompt.service import PromptService

logger = get_logger(__name__)


def make_hook_generation_node(llm: LLMClient | None = None, prompt_service: PromptService | None = None):
    async def hook_generation_node(state: ContentState) -> dict:
        start = time.monotonic()
        strategy_output = state.strategy_output or {}
        topic = strategy_output.get("topic", state.topic or "")
        strategy = strategy_output.get("strategy", {})
        state_errors = list(state.errors)

        if llm and prompt_service:
            try:
                hooks = await _llm_hooks(topic, strategy, state, llm, prompt_service)
            except Exception as exc:
                state_errors.append({"step": "hook_generation", "message": str(exc)})
                logger.warning("hook_generation_node_llm_failed", error=str(exc))
                hooks = _default_hooks(topic)
        else:
            hooks = _default_hooks(topic)

        selected_hook = hooks[0] if hooks else {"text": f"Let's talk about {topic}", "type": "question"}
        latency_ms = int((time.monotonic() - start) * 1000)
        result: dict[str, Any] = {
            "selected_hook": selected_hook,
            "alternatives": hooks[1:],
            "total_hooks": len(hooks),
            "latency_ms": latency_ms,
        }
        return {
            "hooks_output": result,
            "current_step": "hook_generation",
            "errors": state_errors,
            "step_timing": {**state.step_timing, "hook_generation": latency_ms},
        }

    return hook_generation_node


async def _llm_hooks(
    topic: str,
    strategy: dict[str, Any],
    state: ContentState,
    llm: LLMClient,
    prompt_service: PromptService,
) -> list[dict[str, str]]:
    kp = strategy.get("key_points", [])
    system_prompt, user_prompt = prompt_service.build_prompt(
        "hook_generator",
        system_vars={"topic": topic},
        user_vars={
            "topic": topic,
            "angle": strategy.get("angle", ""),
            "key_points": ", ".join(kp) if isinstance(kp, list) else kp,
            "platform": state.platform,
        },
    )
    request = CompletionRequest(
        model="gemini-2.0-flash",
        messages=[ChatMessage(role="user", content=user_prompt)],
        system_prompt=system_prompt,
        temperature=0.8,
        max_tokens=1024,
        response_format="json_object",
    )
    response = await llm.complete(request)
    data = json.loads(response.content)
    return data.get("hooks", [data])


def _default_hooks(topic: str) -> list[dict[str, str]]:
    return [
        {"text": f"Most people get {topic} wrong. Here's what I've learned.", "type": "contrarian"},
        {"text": f"I spent the last month exploring {topic}. Here's what surprised me.", "type": "story"},
        {"text": f"3 things nobody tells you about {topic}:", "type": "list"},
    ]
