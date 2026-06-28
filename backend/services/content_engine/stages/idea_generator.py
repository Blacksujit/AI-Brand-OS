from __future__ import annotations

import json
from typing import Any

from core.llm import ChatMessage, CompletionRequest, LLMClient
from core.logging import get_logger
from services.content_engine.stages.models import (
    AggregatedContext,
    ContentCategory,
    ContentIdea,
)
from services.prompt import PromptService

logger = get_logger(__name__)


class IdeaGenerator:
    """Generates and ranks content ideas from aggregated context."""

    def __init__(self, llm: LLMClient, prompt_service: PromptService | None = None) -> None:
        self._llm = llm
        self._prompt_service = prompt_service or PromptService()

    async def generate(
        self,
        context: AggregatedContext,
        count: int = 5,
        model: str = "gemini-2.0-flash",
    ) -> list[ContentIdea]:
        system_prompt, user_prompt = self._prompt_service.build_prompt(
            "idea_generator",
            user_vars={
                "count": str(count),
                "expertise_areas": ", ".join(context.expertise_areas) if context.expertise_areas else "N/A",
                "trending_topics": ", ".join(context.trending_topics[:10]) if context.trending_topics else "N/A",
                "recent_kb_tags": ", ".join(context.recent_kb_tags[:10]) if context.recent_kb_tags else "N/A",
                "aggregated_summary": (context.aggregated_summary[:500] if context.aggregated_summary else "N/A"),
            },
        )

        request = CompletionRequest(
            model=model,
            messages=[ChatMessage(role="user", content=user_prompt)],
            system_prompt=system_prompt,
            temperature=0.8,
            max_tokens=2048,
            response_format="json_object",
        )

        response = await self._llm.complete(request)
        ideas = self._parse_response(response.content, count)

        for idea in ideas:
            idea.relevance_score = min(
                1.0, idea.relevance_score + context.signal_breakdown.signal_quality * 0.1
            )

        ideas.sort(key=lambda i: i.relevance_score, reverse=True)
        logger.info(
            "idea_generator_generated",
            count=len(ideas),
            model=model,
            tokens=response.usage.total_tokens,
        )
        return ideas[:count]

    def _parse_response(self, content: str, expected: int) -> list[ContentIdea]:
        raw = content.strip()
        if raw.startswith("```"):
            raw = raw.strip("`").strip()
            if raw.startswith("json"):
                raw = raw[4:].strip()
        try:
            data: list[dict[str, Any]] = json.loads(raw)
        except json.JSONDecodeError:
            logger.warning("idea_generator_parse_failed", raw=raw[:200])
            return []

        ideas: list[ContentIdea] = []
        for item in data[:expected]:
            try:
                category = ContentCategory(item.get("category", "opinion"))
            except ValueError:
                category = ContentCategory.OPINION
            ideas.append(
                ContentIdea(
                    title=item.get("title", "Untitled"),
                    description=item.get("description", ""),
                    angle=item.get("angle", ""),
                    category=category,
                    relevance_score=float(item.get("relevance_score", 0.5)),
                    suggested_tone=item.get("suggested_tone", "opinion"),
                    reasoning=item.get("reasoning", ""),
                )
            )
        return ideas
