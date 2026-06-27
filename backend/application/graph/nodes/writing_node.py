from __future__ import annotations

import json
import time
from typing import Any

from application.graph.state import ContentState
from core.llm import ChatMessage, CompletionRequest, LLMClient
from core.logging import get_logger
from services.prompt.service import PromptService

logger = get_logger(__name__)


def make_writing_node(llm: LLMClient | None = None, prompt_service: PromptService | None = None):
    async def writing_node(state: ContentState) -> dict:
        start = time.monotonic()
        strategy_output = state.get("strategy_output") or {}
        hooks_output = state.get("hooks_output") or {}
        topic_output = state.get("topic_output") or {}

        topic = strategy_output.get("topic", state.get("topic", ""))
        strategy = strategy_output.get("strategy", {})
        selected_hook = hooks_output.get("selected_hook", {}).get("text", "")

        if llm:
            draft = await _llm_draft(topic, selected_hook, strategy, state, llm, prompt_service)
        else:
            draft = _default_draft(topic, selected_hook)

        result: dict[str, Any] = {
            "topic": topic,
            "draft": draft,
            "word_count": len(draft.get("body", "").split()),
            "latency_ms": int((time.monotonic() - start) * 1000),
        }
        return {"draft_output": result, "current_step": "writing"}

    return writing_node


async def _llm_draft(
    topic: str,
    hook: str,
    strategy: dict[str, Any],
    state: ContentState,
    llm: LLMClient,
    prompt_service: PromptService | None,
) -> dict[str, str]:
    try:
        kp = strategy.get("key_points", [])
        user_vars = {
            "topic": topic,
            "hook": hook,
            "angle": strategy.get("angle", ""),
            "key_points": ", ".join(kp) if isinstance(kp, list) else str(kp),
            "tone": strategy.get("tone", state.get("tone", "conversational")),
            "target_audience": strategy.get("target_audience", "peers"),
            "platform": state.get("platform", "linkedin"),
            "max_length": str(state.get("max_length", 280)),
        }

        if prompt_service:
            prompt = prompt_service.build_prompt(
                "writing_agent",
                system_vars={"topic": topic, "platform": state.get("platform", "linkedin")},
                user_vars=user_vars,
            )
            system_prompt = prompt.system_prompt
            user_prompt_content = prompt.user_prompt
        else:
            system_prompt = f"You are a professional content writer. Write a post about {topic}."
            user_prompt_content = (
                f"Topic: {topic}\nHook: {hook}\nAngle: {user_vars['angle']}\n"
                f"Key points: {user_vars['key_points']}\n"
                f"Tone: {user_vars['tone']}\nPlatform: {user_vars['platform']}"
            )

        request = CompletionRequest(
            model="gemini-2.0-flash",
            messages=[ChatMessage(role="user", content=user_prompt_content)],
            system_prompt=system_prompt,
            temperature=0.7,
            max_tokens=2048,
            response_format="json_object",
        )
        response = await llm.complete(request)
        return json.loads(response.content)
    except Exception as exc:
        logger.warning("writing_node_llm_failed", error=str(exc))
        return _default_draft(topic, hook)


def _default_draft(topic: str, hook: str) -> dict[str, str]:
    safe_topic = topic or "this trend"
    tag = safe_topic.replace(" ", "")
    body = (
        f"{hook}\n\n"
        f"I've been thinking a lot about {safe_topic} lately. "
        f"It's one of those topics that seems straightforward until you dig deeper.\n\n"
        f"Here's what I've learned:\n\n"
        f"1. Start with why — understand the motivation behind the trend\n"
        f"2. Focus on fundamentals — they don't change even when technology does\n"
        f"3. Share what you learn — teaching others is the best way to solidify understanding\n\n"
        f"What's your experience with {safe_topic}? I'd love to hear your thoughts.\n\n"
        f"#{tag}"
    )
    return {
        "title": f"My take on {safe_topic}",
        "body": body,
        "hashtags": [f"#{tag}", "#Technology", "#Learning"],
        "call_to_action": f"What's your experience with {safe_topic}? Share below!",
    }
