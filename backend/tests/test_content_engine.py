from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from services.content_engine.service import ContentEngine
from services.content_engine.stages.models import (
    AggregatedContext,
    ContentIdea,
    StageContext,
)


@pytest.fixture
def mock_llm() -> MagicMock:
    llm = MagicMock()
    llm.generate = AsyncMock(return_value=MagicMock(content='{"ideas": []}'))
    return llm


class TestContentEngine:
    def test_construct_with_llm(self, mock_llm: MagicMock) -> None:
        engine = ContentEngine(llm=mock_llm)
        assert engine._llm is mock_llm

    @pytest.mark.asyncio
    async def test_generate_ideas_with_context_aggregator(self) -> None:
        engine = ContentEngine(llm=MagicMock(), context_aggregator=MagicMock())
        engine._context_aggregator.aggregate = AsyncMock(
            return_value=AggregatedContext(user_id=uuid.uuid4())
        )
        engine._idea_generator.generate = AsyncMock(return_value=[])
        ideas = await engine.generate_ideas(user_id=uuid.uuid4(), count=3)
        assert isinstance(ideas, list)

    @pytest.mark.asyncio
    async def test_generate_ideas_with_expertise(self) -> None:
        engine = ContentEngine(llm=MagicMock(), context_aggregator=MagicMock())
        engine._context_aggregator.aggregate = AsyncMock(
            return_value=AggregatedContext(user_id=uuid.uuid4())
        )
        engine._idea_generator.generate = AsyncMock(return_value=[])
        ideas = await engine.generate_ideas(
            user_id=uuid.uuid4(),
            count=5,
            expertise_areas=["AI", "marketing"],
        )
        assert isinstance(ideas, list)
        assert engine._context_aggregator.aggregate.called

    @pytest.mark.asyncio
    async def test_run_pipeline_returns_stage_context(self) -> None:
        mock_ctx_agg = MagicMock()
        mock_ctx_agg.aggregate = AsyncMock(return_value=AggregatedContext(user_id=uuid.uuid4()))
        mock_idea_gen = MagicMock()
        mock_idea = ContentIdea(
            title="Test Idea",
            description="A test idea",
            angle="unique perspective",
            relevance_score=0.9,
        )
        mock_idea_gen.generate = AsyncMock(return_value=[mock_idea])
        from services.content_engine.stages.models import (
            CompositionResult,
            QualityDimensions,
            QualityVerdict,
            RefinementResult,
        )

        mock_draft_comp = MagicMock()
        mock_draft_comp.compose = AsyncMock(
            return_value=CompositionResult(
                body="Test body content",
                title="Test",
                hook="Test hook",
                call_to_action="Do it",
                hashtags=["#test"],
                word_count=50,
                draft_id=uuid.uuid4(),
            )
        )
        mock_style = MagicMock()
        mock_style.refine = AsyncMock(
            return_value=RefinementResult(
                original_body="original",
                refined_body="refined",
                changes_applied=[],
            )
        )
        mock_quality = MagicMock()
        mock_quality.evaluate = AsyncMock(
            return_value=QualityVerdict(
                overall_score=0.85,
                verdict="pass",
                dimensions=QualityDimensions(),
            )
        )

        engine = ContentEngine(
            llm=MagicMock(),
            context_aggregator=mock_ctx_agg,
            idea_generator=mock_idea_gen,
            draft_composer=mock_draft_comp,
            style_refiner=mock_style,
            quality_gate=mock_quality,
        )
        result = await engine.run_pipeline(user_id=uuid.uuid4())
        assert isinstance(result, StageContext)
        assert result.composition is not None
        assert result.quality is not None
        assert result.quality.overall_score == 0.85
        assert result.quality.verdict == "pass"

    @pytest.mark.asyncio
    async def test_stage_context_aggregation(self) -> None:
        engine = ContentEngine(llm=MagicMock(), context_aggregator=MagicMock())
        uid = uuid.uuid4()
        ctx = AggregatedContext(
            user_id=uid,
        )
        engine._context_aggregator.aggregate = AsyncMock(return_value=ctx)
        aggregated = await engine._context_aggregator.aggregate(uid)
        assert isinstance(aggregated, AggregatedContext)
        assert aggregated.user_id == uid
