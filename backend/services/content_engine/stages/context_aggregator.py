from __future__ import annotations

import uuid

from core.logging import get_logger
from services.content_engine.stages.models import (
    AggregatedContext,
    SignalBreakdown,
)

logger = get_logger(__name__)


class ContextAggregator:
    """Gathers all context signals for content generation.

    Deterministic — no LLM calls. Collects signals from knowledge
    base and trend services.
    """

    def __init__(self) -> None:
        self._kb_service = None
        self._trend_service = None

    def wire(
        self,
        kb_service: object | None = None,
        trend_service: object | None = None,
    ) -> None:
        self._kb_service = kb_service
        self._trend_service = trend_service

    async def aggregate(self, user_id: uuid.UUID) -> AggregatedContext:
        signals = SignalBreakdown()
        recent_kb_tags: list[str] = []
        trending_topics: list[str] = []

        if self._kb_service:
            try:
                tags = await self._kb_service.get_tags(user_id)
                recent_kb_tags = [t.name for t in tags[:10]] if tags else []
                if recent_kb_tags:
                    signals.has_kb_recent = True
            except Exception as exc:
                logger.warning("context_aggregator_kb_failed", error=str(exc))

        if self._trend_service:
            try:
                trends = await self._trend_service.get_global_trending()
                trending_topics = [t.title for t in trends[:10]] if trends else []
                if trending_topics:
                    signals.has_trends = True
            except Exception as exc:
                logger.warning("context_aggregator_trends_failed", error=str(exc))

        active_count = sum([signals.has_kb_recent, signals.has_trends])
        if active_count >= 2:
            signals.dominant_signal = "mixed"
        elif signals.has_trends:
            signals.dominant_signal = "trends"
        elif signals.has_kb_recent:
            signals.dominant_signal = "knowledge"
        signals.signal_quality = min(1.0, active_count / 2.0)

        all_topics = list(set(recent_kb_tags + trending_topics))

        return AggregatedContext(
            user_id=user_id,
            recent_kb_tags=recent_kb_tags,
            trending_topics=trending_topics,
            aggregated_summary=" | ".join(all_topics[:20]) if all_topics else "",
            signal_breakdown=signals,
        )
