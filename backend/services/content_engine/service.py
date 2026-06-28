from __future__ import annotations

import uuid

from core.llm import LLMClient
from core.logging import get_logger
from services.content_engine.stages import (
    CompositionParams,
    CompositionResult,
    ContentIdea,
    ContextAggregator,
    DraftComposer,
    IdeaGenerator,
    QualityGate,
    StageContext,
    StyleRefiner,
)
from services.knowledge import KnowledgeBaseService
from services.prompt import PromptService
from services.trend import TrendService

logger = get_logger(__name__)


class ContentEngine:
    """Orchestrates the 5-stage content generation pipeline."""

    def __init__(
        self,
        llm: LLMClient,
        context_aggregator: ContextAggregator | None = None,
        idea_generator: IdeaGenerator | None = None,
        draft_composer: DraftComposer | None = None,
        style_refiner: StyleRefiner | None = None,
        quality_gate: QualityGate | None = None,
        kb_service: KnowledgeBaseService | None = None,
        trend_service: TrendService | None = None,
        prompt_service: PromptService | None = None,
    ) -> None:
        self._llm = llm
        
        if prompt_service is None:
            prompt_service = PromptService()
        self._prompt_service = prompt_service
        
        if context_aggregator is None:
            context_aggregator = ContextAggregator()
        
        if kb_service or trend_service:
            context_aggregator.wire(
                kb_service=kb_service,
                trend_service=trend_service,
            )
        self._context_aggregator = context_aggregator
        
        self._idea_generator = idea_generator or IdeaGenerator(llm, prompt_service=prompt_service)
        self._draft_composer = draft_composer or DraftComposer(llm, prompt_service=prompt_service)
        self._style_refiner = style_refiner or StyleRefiner()
        self._quality_gate = quality_gate or QualityGate(llm, prompt_service=prompt_service)

    async def generate_ideas(
        self,
        user_id: uuid.UUID,
        count: int = 5,
        expertise_areas: list[str] | None = None,
    ) -> list[ContentIdea]:
        context = await self._context_aggregator.aggregate(user_id)
        if expertise_areas:
            context.expertise_areas = expertise_areas
        return await self._idea_generator.generate(context, count=count)

    async def generate_draft(
        self,
        user_id: uuid.UUID,
        idea: ContentIdea,
        params: CompositionParams | None = None,
        run_quality_gate: bool = True,
    ) -> CompositionResult:
        context = await self._context_aggregator.aggregate(user_id)
        stage = StageContext(
            user_id=user_id,
            aggregated_context=context,
            selected_idea=idea,
            params=params or CompositionParams(),
        )

        stage.composition = await self._draft_composer.compose(
            idea=idea,
            context=context,
            params=stage.params,
        )
        logger.info(
            "content_engine_draft_composed",
            draft_id=str(stage.composition.draft_id),
            word_count=stage.composition.word_count,
        )

        stage.refinement = await self._style_refiner.refine(stage.composition)
        if stage.refinement.changes_applied:
            logger.info(
                "content_engine_refined",
                changes=len(stage.refinement.changes_applied),
            )

        if run_quality_gate:
            stage.quality = await self._quality_gate.evaluate(stage.composition, context)
            logger.info(
                "content_engine_quality",
                verdict=stage.quality.verdict,
                score=stage.quality.overall_score,
            )

        return stage.composition

    async def run_pipeline(
        self,
        user_id: uuid.UUID,
        params: CompositionParams | None = None,
        expertise_areas: list[str] | None = None,
    ) -> StageContext:
        """Run the full pipeline end-to-end and return the complete stage context."""
        context = await self._context_aggregator.aggregate(user_id)
        if expertise_areas:
            context.expertise_areas = expertise_areas

        ideas = await self._idea_generator.generate(context)
        if not ideas:
            logger.warning("content_engine_no_ideas", user_id=str(user_id))
            return StageContext(user_id=user_id, aggregated_context=context)

        best_idea = ideas[0]
        p = params or CompositionParams()

        composition = await self._draft_composer.compose(idea=best_idea, context=context, params=p)
        refinement = await self._style_refiner.refine(composition)
        quality = await self._quality_gate.evaluate(composition, context)

        return StageContext(
            user_id=user_id,
            aggregated_context=context,
            ideas=ideas,
            selected_idea=best_idea,
            composition=composition,
            refinement=refinement,
            quality=quality,
            params=p,
        )