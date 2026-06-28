from __future__ import annotations

import uuid
from collections import Counter
from datetime import UTC, datetime

from pydantic import BaseModel, Field

from core.logging import get_logger
from services.trend import TrendService

logger = get_logger(__name__)


class ResearchFinding(BaseModel):
    title: str
    description: str
    source: str
    url: str | None = None
    relevance_score: float = 0.5
    freshness_score: float = 0.5
    matched_expertise: list[str] = Field(default_factory=list)
    discovered_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ResearchSummary(BaseModel):
    findings: list[ResearchFinding] = Field(default_factory=list)
    sources_queried: int = 0
    duration_ms: int = 0

    @property
    def total_findings(self) -> int:
        return len(self.findings)

    @property
    def dominant_theme(self) -> str | None:
        if not self.findings:
            return None
        keywords: list[str] = []
        for f in self.findings:
            keywords.extend(f.title.lower().split()[:5])
            keywords.extend(f.description.lower().split()[:5])
        if keywords:
            common = Counter(keywords).most_common(3)
            return " ".join(k for k, _ in common)
        return None


class ResearchService:
    """Discovers trending topics and relevant content for content generation."""

    def __init__(self) -> None:
        self._trend_service: TrendService | None = None

    def wire(self, trend_service: TrendService | None = None) -> None:
        self._trend_service = trend_service

    async def research(
        self,
        user_id: uuid.UUID,
        expertise_areas: list[str] | None = None,
        max_findings: int = 15,
        lookback_hours: int = 24,
    ) -> ResearchSummary:
        import time

        start = time.monotonic()

        findings: list[ResearchFinding] = []

        if self._trend_service:
            try:
                trends = await self._trend_service.get_trending_topics(limit=max_findings)
                for t in (trends or [])[:max_findings]:
                    findings.append(
                        ResearchFinding(
                            title=t.name,
                            description=t.description or "",
                            source="trends",
                            url="",
                            relevance_score=t.velocity,
                            freshness_score=0.5,
                        )
                    )
            except Exception as exc:
                logger.warning("research_trends_failed", error=str(exc))

        if expertise_areas:
            scored: list[ResearchFinding] = []
            for f in findings:
                matched = [
                    ea
                    for ea in expertise_areas
                    if ea.lower() in f.title.lower() or ea.lower() in f.description.lower()
                ]
                f.matched_expertise = matched
                if matched:
                    f.relevance_score = min(1.0, f.relevance_score + 0.2)
                scored.append(f)
            findings = scored
            findings.sort(key=lambda f: f.relevance_score, reverse=True)

        elapsed = int((time.monotonic() - start) * 1000)

        return ResearchSummary(
            findings=findings[:max_findings],
            sources_queried=1 if self._trend_service else 0,
            duration_ms=elapsed,
        )

    async def get_context_for_agent(
        self,
        user_id: uuid.UUID,
        expertise_areas: list[str] | None = None,
    ) -> list[dict]:
        summary = await self.research(user_id, expertise_areas)
        return [f.model_dump() for f in summary.findings]
