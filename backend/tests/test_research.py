from __future__ import annotations

import uuid

import pytest

from services.research import ResearchFinding, ResearchService, ResearchSummary


@pytest.fixture
def research_service() -> ResearchService:
    return ResearchService()


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
