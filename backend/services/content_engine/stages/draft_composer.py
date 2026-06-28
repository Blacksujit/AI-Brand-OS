from __future__ import annotations

import uuid
from typing import Any

from core.llm import ChatMessage, CompletionRequest, LLMClient
from core.logging import get_logger
from services.content_engine.stages.models import (
    AggregatedContext,
    CompositionParams,
    CompositionResult,
    ContentIdea,
)
from services.prompt import PromptService

logger = get_logger(__name__)


class DraftComposer:
    """Composes full draft content from an idea and context."""

    def __init__(self, llm: LLMClient, prompt_service: PromptService | None = None) -> None:
        self._llm = llm
        self._prompt_service = prompt_service or PromptService()

    async def compose(
        self,
        idea: ContentIdea,
        context: AggregatedContext,
        params: CompositionParams | None = None,
        model: str = "gemini-2.0-flash",
    ) -> CompositionResult:
        p = params or CompositionParams()
        start = __import__("time").time()

        anecdote_line = ""
        if p.include_personal_anecdote:
            anecdote_line = "Include a personal anecdote or real experience where relevant."

        system_prompt, user_prompt = self._prompt_service.build_prompt(
            "draft_composer",
            user_vars={
                "platform": p.platform,
                "title": idea.title,
                "description": idea.description,
                "angle": idea.angle,
                "category": idea.category.value,
                "tone": p.tone,
                "target_audience": p.target_audience,
                "length": p.length,
                "include_personal_anecdote": anecdote_line,
                "aggregated_summary": (context.aggregated_summary[:500] if context.aggregated_summary else "N/A"),
                "expertise_areas": ", ".join(context.expertise_areas) if context.expertise_areas else "N/A",
            },
        )

        request = CompletionRequest(
            model=model,
            messages=[ChatMessage(role="user", content=user_prompt)],
            system_prompt=system_prompt,
            temperature=p.creativity_level,
            max_tokens=2048,
            response_format="json_object",
        )

        response = await self._llm.complete(request)
        elapsed_ms = int((__import__("time").time() - start) * 1000)
        data = self._parse_response(response.content)
        word_count = len(data.get("body", "").split())

        return CompositionResult(
            draft_id=uuid.uuid4(),
            title=data.get("title", idea.title),
            body=data.get("body", ""),
            hook=data.get("hook", ""),
            call_to_action=data.get("call_to_action", ""),
            hashtags=data.get("hashtags", []),
            word_count=word_count,
            reading_time_seconds=max(1, word_count // 4),
            llm_used=model,
            tokens_used=response.usage.total_tokens,
            composition_duration_ms=elapsed_ms,
            has_code_blocks="```" in data.get("body", ""),
            sections=data.get("sections", []),
        )

    def _parse_response(self, content: str) -> dict[str, Any]:
        raw = content.strip()
        if raw.startswith("```"):
            raw = raw.strip("`").strip()
            if raw.startswith("json"):
                raw = raw[4:].strip()
        import json

        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            logger.warning("draft_composer_parse_failed", raw=raw[:200])
            return {"title": "", "body": raw, "hook": "", "call_to_action": "", "hashtags": []}
