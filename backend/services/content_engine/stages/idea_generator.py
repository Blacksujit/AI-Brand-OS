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

logger = get_logger(__name__)

IDEA_SYSTEM_PROMPT = """You are a content strategist who generates relevant content ideas.
Given a user's context signals (trends, knowledge base tags, GitHub activity, expertise areas),
generate creative but relevant content ideas.

For each idea provide:
1. title — short, compelling headline
2. description — 1-2 sentence explanation
3. angle — the unique perspective or hook
4. category — one of: tutorial, opinion, project_update, paper_summary, industry_analysis, personal_story, code_deep_dive
5. relevance_score — 0.0-1.0 how relevant this is to their expertise
6. suggested_tone — educational, opinion, insight, tutorial, or story
7. reasoning — why this idea is relevant right now

Respond ONLY with a valid JSON array of objects. No markdown, no commentary."""


class IdeaGenerator:
    """Generates and ranks content ideas from aggregated context."""

    def __init__(self, llm: LLMClient) -> None:
        self._llm = llm

    async def generate(
        self,
        context: AggregatedContext,
        count: int = 5,
        model: str = "gemini-2.0-flash",
    ) -> list[ContentIdea]:
        user_prompt = self._build_user_prompt(context, count)

        request = CompletionRequest(
            model=model,
            messages=[ChatMessage(role="user", content=user_prompt)],
            system_prompt=IDEA_SYSTEM_PROMPT,
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

    def _build_user_prompt(self, context: AggregatedContext, count: int) -> str:
        lines = [f"Generate up to {count} content ideas based on this context:"]
        if context.expertise_areas:
            lines.append(f"Expertise areas: {', '.join(context.expertise_areas)}")
        if context.trending_topics:
            lines.append(f"Trending topics: {', '.join(context.trending_topics[:10])}")
        if context.recent_kb_tags:
            lines.append(f"Knowledge base tags: {', '.join(context.recent_kb_tags[:10])}")
        if context.recent_github_topics:
            lines.append(f"GitHub activity: {', '.join(context.recent_github_topics[:5])}")
        if context.aggregated_summary:
            lines.append(f"Context summary: {context.aggregated_summary[:500]}")
        return "\n".join(lines)

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
