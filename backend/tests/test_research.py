from __future__ import annotations

import uuid
from unittest.mock import AsyncMock

import pytest

from services.research import ResearchFinding, ResearchService, ResearchSummary


@pytest.fixture
def research_service() -> ResearchService:
    return ResearchService()


def _make_trend_topic(name: str, description: str, velocity: float = 0.5):
    """Build a trend-topic-like object with the attrs ResearchService uses."""
    return type("FakeTrendTopic", (), {"name": name, "description": description, "velocity": velocity})()


class TestResearchService:
    @pytest.mark.asyncio
    async def test_research_without_trend_service(self, research_service) -> None:
        summary = await research_service.research(user_id=uuid.uuid4())
        assert isinstance(summary, ResearchSummary)
        assert summary.findings == []

    @pytest.mark.asyncio
    async def test_research_with_expertise(self, research_service) -> None:
        summary = await research_service.research(
            user_id=uuid.uuid4(),
            expertise_areas=["AI", "marketing"],
        )
        assert isinstance(summary, ResearchSummary)

    @pytest.mark.asyncio
    async def test_research_with_wired_trend_service(self, research_service) -> None:
        mock_trend = AsyncMock()
        mock_trend.get_trending_topics.return_value = [
            _make_trend_topic("AI in Marketing", "Using AI for marketing campaigns", 0.9),
            _make_trend_topic("Quantum Computing", "Latest advances in QC", 0.4),
        ]
        research_service.wire(trend_service=mock_trend)
        summary = await research_service.research(
            user_id=uuid.uuid4(),
            expertise_areas=["marketing"],
        )
        assert len(summary.findings) == 2
        assert summary.sources_queried == 1
        ai_finding = next(f for f in summary.findings if "AI" in f.title)
        assert ai_finding.relevance_score > 0.5
        assert "marketing" in ai_finding.matched_expertise

    @pytest.mark.asyncio
    async def test_research_trend_service_raises(self, research_service) -> None:
        mock_trend = AsyncMock()
        mock_trend.get_trending_topics.side_effect = RuntimeError("API down")
        research_service.wire(trend_service=mock_trend)
        summary = await research_service.research(user_id=uuid.uuid4())
        assert summary.findings == []
        assert summary.sources_queried == 1

    @pytest.mark.asyncio
    async def test_get_context_for_agent(self, research_service) -> None:
        context = await research_service.get_context_for_agent(
            user_id=uuid.uuid4(),
            expertise_areas=["technology"],
        )
        assert isinstance(context, list)

    @pytest.mark.asyncio
    async def test_research_finding_creation(self) -> None:
        finding = ResearchFinding(
            title="AI Marketing Trends",
            description="Latest trends in AI marketing",
            source="web",
            url="https://example.com",
            relevance_score=0.9,
            freshness_score=0.8,
            matched_expertise=["AI", "marketing"],
        )
        assert finding.title == "AI Marketing Trends"
        assert finding.relevance_score == 0.9

    @pytest.mark.asyncio
    async def test_research_summary_empty(self) -> None:
        summary = ResearchSummary(findings=[])
        assert summary.total_findings == 0
        assert summary.dominant_theme is None

    @pytest.mark.asyncio
    async def test_research_summary_dominant_theme(self) -> None:
        summary = ResearchSummary(
            findings=[
                ResearchFinding(title="AI Trends", description="Advances in AI", source="web"),
                ResearchFinding(title="Machine Learning", description="ML models", source="web"),
            ]
        )
        assert summary.total_findings == 2
        assert summary.dominant_theme is not None
        assert "ai" in summary.dominant_theme
