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

logger = get_logger(__name__)

COMPOSER_SYSTEM_PROMPT = """You are a professional content writer. Given a content idea and context, write a compelling post.

Rules:
- Write in a natural, human voice — never robotic or overly formal
- Use short paragraphs (1-3 sentences) for social media readability
- Include a strong hook in the first line
- End with a call to action or thought-provoking question
- Add relevant hashtags at the end (3-5)
- Keep the tone consistent throughout
- Never use AI clichés like "delve into," "let's dive in," "it's worth noting"
- Write like a real person sharing their genuine experience and insight

Respond with a JSON object:
{
  "title": "Post title",
  "body": "Full post body",
  "hook": "Opening hook sentence",
  "call_to_action": "Closing CTA",
  "hashtags": ["#tag1", "#tag2", "#tag3"],
  "sections": ["section1", "section2"]
}"""


class DraftComposer:
    """Composes full draft content from an idea and context."""

    def __init__(self, llm: LLMClient) -> None:
        self._llm = llm

    async def compose(
        self,
        idea: ContentIdea,
        context: AggregatedContext,
        params: CompositionParams | None = None,
        model: str = "gemini-2.0-flash",
    ) -> CompositionResult:
        p = params or CompositionParams()
        user_prompt = self._build_user_prompt(idea, context, p)
        start = __import__("time").time()

        request = CompletionRequest(
            model=model,
            messages=[ChatMessage(role="user", content=user_prompt)],
            system_prompt=COMPOSER_SYSTEM_PROMPT,
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

    def _build_user_prompt(
        self,
        idea: ContentIdea,
        context: AggregatedContext,
        params: CompositionParams,
    ) -> str:
        lines = [f"Write a {params.platform} post based on this idea:\n"]
        lines.append(f"Title: {idea.title}")
        lines.append(f"Description: {idea.description}")
        lines.append(f"Angle: {idea.angle}")
        lines.append(f"Category: {idea.category.value}")
        lines.append(f"Suggested tone: {params.tone}")
        lines.append(f"Target audience: {params.target_audience}")
        lines.append(f"Length: {params.length}")

        if context.aggregated_summary:
            lines.append(f"\nContext: {context.aggregated_summary[:500]}")
        if context.expertise_areas:
            lines.append(f"\nExpertise areas: {', '.join(context.expertise_areas)}")

        if params.include_personal_anecdote:
            lines.append("\nInclude a personal anecdote or real experience where relevant.")

        return "\n".join(lines)

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
