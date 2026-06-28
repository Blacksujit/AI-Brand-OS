from __future__ import annotations

import json
import time

from application.graph.state import ContentState
from core.llm import ChatMessage, CompletionRequest, LLMClient
from core.logging import get_logger
from services.prompt.service import PromptService

logger = get_logger(__name__)


def make_review_node(llm: LLMClient | None = None, prompt_service: PromptService | None = None):
    async def review_node(state: ContentState) -> dict:
        start = time.monotonic()
        draft_output = state.get("draft_output") or {}
        draft = draft_output.get("draft", {})
        body = draft.get("body", "")
        topic = draft_output.get("topic", state.get("topic", ""))

        if llm and body:
            review = await _llm_review(body, topic, llm, prompt_service)
        else:
            review = _heuristic_review(body)

        verdict = review.get("verdict", "minor_changes")
        score = review.get("score", 0.5)
        recommended_action = review.get("recommended_action", "revise")

        result = {
            "topic": topic,
            "verdict": verdict,
            "score": score,
            "feedback": review.get("feedback", ""),
            "issues": review.get("issues", []),
            "recommended_action": recommended_action,
            "requires_regeneration": recommended_action == "reject",
            "latency_ms": int((time.monotonic() - start) * 1000),
        }
        requires_human = recommended_action in ("revise", "major_revision", "reject")
        return {
            "review_output": result,
            "current_step": "review",
            "requires_human_approval": requires_human,
        }

    return review_node


async def _llm_review(
    body: str, topic: str, llm: LLMClient, prompt_service: PromptService | None
) -> dict:
    try:
        if prompt_service:
            system_prompt, user_prompt_content = prompt_service.build_prompt(
                "review_agent",
                system_vars={"topic": topic},
                user_vars={"topic": topic, "post_body": body[:3000]},
            )
        else:
            system_prompt = "You are a content quality reviewer. Review the post and return JSON."
            user_prompt_content = f"Topic: {topic}\n\nPost:\n{body[:3000]}"

        request = CompletionRequest(
            model="gemini-2.0-flash",
            messages=[ChatMessage(role="user", content=user_prompt_content)],
            system_prompt=system_prompt,
            temperature=0.3,
            max_tokens=1024,
            response_format="json_object",
        )
        response = await llm.complete(request)
        return json.loads(response.content)
    except Exception as exc:
        logger.warning("review_node_llm_failed", error=str(exc))
        return _heuristic_review(body)


def _heuristic_review(body: str) -> dict:
    word_count = len(body.split())
    verdict = "pass"
    score = 0.7
    issues = []

    if word_count < 50:
        verdict = "major_revision"
        score = 0.3
        issues.append(
            {
                "severity": "critical",
                "aspect": "length",
                "suggestion": "Post is too short — expand with more detail and examples",
            }
        )
    elif word_count < 100:
        verdict = "minor_changes"
        score = 0.5
        issues.append(
            {
                "severity": "minor",
                "aspect": "length",
                "suggestion": "Consider adding more depth",
            }
        )

    return {
        "verdict": verdict,
        "score": score,
        "feedback": f"Post is {word_count} words. {'Looks good' if verdict == 'pass' else 'Needs improvement'}.",
        "issues": issues,
        "recommended_action": "approve" if verdict == "pass" else "revise",
    }
