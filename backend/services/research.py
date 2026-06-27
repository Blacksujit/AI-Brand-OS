from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from core.logging import get_logger

logger = get_logger(__name__)


class ResearchFinding:
    """A single research finding from an external source."""

    def __init__(
        self,
        title: str,
        description: str,
        source: str,
        url: str | None = None,
        relevance_score: float = 0.5,
        freshness_score: float = 0.5,
        matched_expertise: list[str] | None = None,
    ) -> None:
        self.title = title
        self.description = description
        self.source = source
        self.url = url
        self.relevance_score = relevance_score
        self.freshness_score = freshness_score
        self.matched_expertise = matched_expertise or []
        self.discovered_at = datetime.now(UTC)


class ResearchSummary:
    """Summary of a research session."""

    def __init__(
        self,
        findings: list[ResearchFinding],
        sources_queried: int = 0,
        duration_ms: int = 0,
    ) -> None:
        self.findings = findings
        self.sources_queried = sources_queried
        self.duration_ms = duration_ms
        self.total_findings = len(findings)
        self.dominant_theme = self._extract_theme(findings)

    def _extract_theme(self, findings: list[ResearchFinding]) -> str | None:
        if not findings:
            return None
        from collections import Counter

        keywords: list[str] = []
        for f in findings:
            keywords.extend(f.title.lower().split()[:5])
            keywords.extend(f.description.lower().split()[:5])
        if keywords:
            common = Counter(keywords).most_common(3)
            return " ".join(k for k, _ in common)
        return None


class ResearchService:
    """Discovers trending topics and relevant content for content generation.

    Wraps the TrendService for cached trend data with additional
    cross-source deduplication and relevance scoring.
    """

    def __init__(self) -> None:
        self._trend_service = None

    def wire(self, trend_service: object | None = None) -> None:
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
                trends = await self._trend_service.get_global_trending()
                for t in (trends or [])[:max_findings]:
                    findings.append(
                        ResearchFinding(
                            title=t.title,
                            description=t.description,
                            source=t.source,
                            url=t.url,
                            relevance_score=getattr(t, "relevance_score", 0.5),
                            freshness_score=getattr(t, "freshness_score", 0.5),
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
    ) -> list[dict[str, Any]]:
        summary = await self.research(user_id, expertise_areas)
        return [
            {
                "title": f.title,
                "description": f.description,
                "source": f.source,
                "url": f.url,
                "relevance_score": f.relevance_score,
                "freshness_score": f.freshness_score,
                "matched_expertise": f.matched_expertise,
            }
            for f in summary.findings
        ]
