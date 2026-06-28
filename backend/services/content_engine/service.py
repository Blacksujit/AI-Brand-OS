from __future__ import annotations

import uuid

from core.logging import get_logger
from services.content_engine.stages import ContentIdea, ContextAggregator, IdeaGenerator
from services.knowledge import KnowledgeBaseService
from services.trend import TrendService

logger = get_logger(__name__)


class ContentEngine:
    """Legacy wrapper — idea generation only. Pipeline moved to LangGraph."""

    def __init__(
        self,
        context_aggregator: ContextAggregator | None = None,
        idea_generator: IdeaGenerator | None = None,
        kb_service: KnowledgeBaseService | None = None,
        trend_service: TrendService | None = None,
    ) -> None:
        self._context_aggregator = context_aggregator or ContextAggregator()
        if kb_service or trend_service:
            self._context_aggregator.wire(
                kb_service=kb_service,
                trend_service=trend_service,
            )
        self._idea_generator = idea_generator

    async def generate_ideas(
        self,
        user_id: uuid.UUID,
        count: int = 5,
        expertise_areas: list[str] | None = None,
    ) -> list[ContentIdea]:
        context = await self._context_aggregator.aggregate(user_id)
        if expertise_areas:
            context.expertise_areas = expertise_areas
        if self._idea_generator:
            return await self._idea_generator.generate(context, count=count)
        return []
