from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from services.content_engine.service import ContentEngine
from services.content_engine.stages.models import (
    AggregatedContext,
    ContentIdea,
)


class TestContentEngine:
    @pytest.mark.asyncio
    async def test_generate_ideas_with_context_aggregator(self) -> None:
        engine = ContentEngine(context_aggregator=MagicMock(), idea_generator=MagicMock())
        engine._context_aggregator.aggregate = AsyncMock(
            return_value=AggregatedContext(user_id=uuid.uuid4())
        )
        engine._idea_generator.generate = AsyncMock(return_value=[])
        ideas = await engine.generate_ideas(user_id=uuid.uuid4(), count=3)
        assert isinstance(ideas, list)

    @pytest.mark.asyncio
    async def test_generate_ideas_with_expertise(self) -> None:
        engine = ContentEngine(context_aggregator=MagicMock(), idea_generator=MagicMock())
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
    async def test_stage_context_aggregation(self) -> None:
        engine = ContentEngine(context_aggregator=MagicMock())
        uid = uuid.uuid4()
        ctx = AggregatedContext(
            user_id=uid,
        )
        engine._context_aggregator.aggregate = AsyncMock(return_value=ctx)
        aggregated = await engine._context_aggregator.aggregate(uid)
        assert isinstance(aggregated, AggregatedContext)
        assert aggregated.user_id == uid
