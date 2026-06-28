from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from services.content_engine.stages.context_aggregator import ContextAggregator
from services.content_engine.stages.draft_composer import DraftComposer
from services.content_engine.stages.models import (
    AggregatedContext,
    CompositionParams,
    CompositionResult,
    ContentCategory,
    ContentIdea,
)
from services.content_engine.stages.quality_gate import QualityGate
from services.content_engine.stages.style_refiner import StyleRefiner


class TestContextAggregator:
    async def test_aggregate_no_services(self) -> None:
        agg = ContextAggregator()
        result = await agg.aggregate(uuid.uuid4())
        assert isinstance(result, AggregatedContext)
        assert result.recent_kb_tags == []
        assert result.trending_topics == []
        assert result.signal_breakdown.dominant_signal == "mixed"
        assert result.signal_breakdown.signal_quality == 0.0

    async def test_aggregate_with_kb_service(self) -> None:
        agg = ContextAggregator()
        mock_kb = MagicMock()
        mock_tag = MagicMock()
        mock_tag.name = "python"
        mock_kb.get_tags = AsyncMock(return_value=[mock_tag])
        agg.wire(kb_service=mock_kb)
        result = await agg.aggregate(uuid.uuid4())
        assert result.recent_kb_tags == ["python"]
        assert result.signal_breakdown.has_kb_recent is True

    async def test_aggregate_with_trend_service(self) -> None:
        agg = ContextAggregator()
        mock_trend = MagicMock()
        mock_trend_item = MagicMock()
        mock_trend_item.name = "AI Agents"
        mock_trend.get_trending_topics = AsyncMock(return_value=[mock_trend_item])
        agg.wire(trend_service=mock_trend)
        result = await agg.aggregate(uuid.uuid4())
        assert result.trending_topics == ["AI Agents"]
        assert result.signal_breakdown.has_trends is True

    async def test_aggregate_kb_failure_does_not_block(self) -> None:
        agg = ContextAggregator()
        mock_kb = MagicMock()
        mock_kb.get_tags = AsyncMock(side_effect=ValueError("DB gone"))
        agg.wire(kb_service=mock_kb)
        result = await agg.aggregate(uuid.uuid4())
        assert result.recent_kb_tags == []
        assert result.signal_breakdown.has_kb_recent is False

    async def test_aggregate_combined_signals(self) -> None:
        agg = ContextAggregator()
        mock_kb = MagicMock()
        mock_tag = MagicMock()
        mock_tag.name = "python"
        mock_kb.get_tags = AsyncMock(return_value=[mock_tag])
        mock_trend = MagicMock()
        mock_trend_item = MagicMock()
        mock_trend_item.name = "AI Agents"
        mock_trend.get_trending_topics = AsyncMock(return_value=[mock_trend_item])
        agg.wire(kb_service=mock_kb, trend_service=mock_trend)
        result = await agg.aggregate(uuid.uuid4())
        assert result.recent_kb_tags == ["python"]
        assert result.trending_topics == ["AI Agents"]
        assert result.signal_breakdown.dominant_signal == "mixed"
        assert result.signal_breakdown.signal_quality == 1.0
        assert "python" in result.aggregated_summary
        assert "AI Agents" in result.aggregated_summary

    async def test_aggregate_trend_failure_does_not_block(self) -> None:
        agg = ContextAggregator()
        mock_trend = MagicMock()
        mock_trend.get_trending_topics = AsyncMock(side_effect=RuntimeError("API down"))
        agg.wire(trend_service=mock_trend)
        result = await agg.aggregate(uuid.uuid4())
        assert result.trending_topics == []
        assert result.signal_breakdown.has_trends is False


class TestDraftComposer:
    def test_parse_valid_json(self) -> None:
        dc = DraftComposer(llm=MagicMock())
        raw = '{"title": "Test", "body": "Hello", "hook": "Wow", "call_to_action": "Do it", "hashtags": ["#test"], "sections": ["intro"]}'
        result = dc._parse_response(raw)
        assert result["title"] == "Test"
        assert result["body"] == "Hello"
        assert result["hook"] == "Wow"
        assert result["hashtags"] == ["#test"]

    def test_parse_json_in_code_fence(self) -> None:
        dc = DraftComposer(llm=MagicMock())
        raw = '```json\n{"title": "Test", "body": "Body"}\n```'
        result = dc._parse_response(raw)
        assert result["title"] == "Test"
        assert result["body"] == "Body"

    def test_parse_malformed_json_returns_fallback(self) -> None:
        dc = DraftComposer(llm=MagicMock())
        raw = "This is not JSON at all"
        result = dc._parse_response(raw)
        assert result["title"] == ""
        assert result["body"] == raw

    def test_parse_empty_string_returns_raw_body(self) -> None:
        dc = DraftComposer(llm=MagicMock())
        result = dc._parse_response("")
        assert result["title"] == ""
        assert result["body"] == ""


class TestStyleRefiner:
    async def test_no_cliches_no_changes(self) -> None:
        refiner = StyleRefiner()
        result = MagicMock(spec=CompositionResult)
        result.body = "This is clean text without any cliches."
        result.hook = ""
        refinement = await refiner.refine(result)
        assert len(refinement.changes_applied) == 0

    async def test_replaces_known_ai_cliches(self) -> None:
        refiner = StyleRefiner()
        result = MagicMock(spec=CompositionResult)
        result.body = "Let's leverage AI to revolutionize our workflow."
        result.hook = ""
        refinement = await refiner.refine(result)
        assert "use" in refinement.refined_body
        assert "change" in refinement.refined_body
        assert "leverage" not in refinement.refined_body
        assert "revolutionize" not in refinement.refined_body
        assert len(refinement.changes_applied) >= 2

    async def test_removes_filler_phrases(self) -> None:
        refiner = StyleRefiner()
        result = MagicMock(spec=CompositionResult)
        result.body = "In today's digital landscape, it's worth noting that AI matters."
        result.hook = ""
        refinement = await refiner.refine(result)
        assert "it's worth noting" not in refinement.refined_body
        assert "in today's digital landscape" not in refinement.refined_body.lower()

    async def test_hook_inserted_when_missing(self) -> None:
        refiner = StyleRefiner()
        result = MagicMock(spec=CompositionResult)
        result.body = "Some content here."
        result.hook = "Amazing hook!"
        refinement = await refiner.refine(result)
        assert refinement.refined_body.startswith("Amazing hook!")
        assert any(c.change_type == "hook_insertion" for c in refinement.changes_applied)

    async def test_hook_not_duplicated_when_already_present(self) -> None:
        refiner = StyleRefiner()
        result = MagicMock(spec=CompositionResult)
        result.body = "Amazing hook!\n\nSome content here."
        result.hook = "Amazing hook!"
        refinement = await refiner.refine(result)
        count = sum(1 for c in refinement.changes_applied if c.change_type == "hook_insertion")
        assert count == 0

    async def test_style_score_decreases_with_more_changes(self) -> None:
        refiner = StyleRefiner()
        result = MagicMock(spec=CompositionResult)
        result.body = "Leverage AI to revolutionize our workflow. Utilize cutting-edge tools."
        result.hook = ""
        refinement = await refiner.refine(result)
        assert refinement.style_adherence_score < 1.0
        assert refinement.style_adherence_score > 0.0

    async def test_preserves_original_body(self) -> None:
        refiner = StyleRefiner()
        result = MagicMock(spec=CompositionResult)
        result.body = "Original text here."
        result.hook = ""
        refinement = await refiner.refine(result)
        assert refinement.original_body == "Original text here."

    async def test_refine_full_delegates_to_refine(self) -> None:
        refiner = StyleRefiner()
        result = MagicMock(spec=CompositionResult)
        result.body = "Some text."
        result.hook = ""
        a = await refiner.refine(result)
        b = await refiner.refine_full(result)
        assert a.refined_body == b.refined_body
        assert len(a.changes_applied) == len(b.changes_applied)


def _make_llm_mock(response_content: str = '{"overall_score": 0.9, "verdict": "pass", "dimensions": {}, "warnings": [], "recommendations": []}') -> MagicMock:
    llm = MagicMock()
    response = MagicMock()
    response.content = response_content
    llm.complete = AsyncMock(return_value=response)
    return llm


class TestQualityGate:
    def test_parse_valid_json(self) -> None:
        qg = QualityGate(llm=_make_llm_mock())
        raw = '{"overall_score": 0.85, "verdict": "pass", "dimensions": {"readability": 0.9}, "warnings": [], "recommendations": ["Add more data"]}'
        result = qg._parse_response(raw)
        assert result["overall_score"] == 0.85
        assert result["verdict"] == "pass"
        assert result["recommendations"] == ["Add more data"]

    def test_parse_json_in_code_fence(self) -> None:
        qg = QualityGate(llm=_make_llm_mock())
        raw = '```json\n{"overall_score": 0.9, "verdict": "pass"}\n```'
        result = qg._parse_response(raw)
        assert result["overall_score"] == 0.9

    def test_parse_malformed_returns_safe_defaults(self) -> None:
        qg = QualityGate(llm=_make_llm_mock())
        raw = "not json"
        result = qg._parse_response(raw)
        assert result["overall_score"] == 0.5
        assert result["verdict"] == "warn"

    async def test_evaluate_short_body_fails(self) -> None:
        qg = QualityGate(llm=_make_llm_mock())
        comp = MagicMock(spec=CompositionResult)
        comp.body = "Too short"
        comp.title = "Test"
        comp.hook = ""
        comp.call_to_action = ""
        comp.hashtags = []
        comp.has_code_blocks = False
        verdict = await qg.evaluate(comp)
        assert verdict.verdict == "fail"
        assert any(w.category == "length" for w in verdict.warnings)

    async def test_evaluate_incomplete_code_blocks_warns(self) -> None:
        qg = QualityGate(llm=_make_llm_mock())
        comp = MagicMock(spec=CompositionResult)
        comp.body = "Some code: ```python\nprint('hello')"
        comp.title = "Test"
        comp.hook = ""
        comp.call_to_action = ""
        comp.hashtags = []
        comp.has_code_blocks = True
        verdict = await qg.evaluate(comp)
        assert verdict.verdict == "warn"
        assert any(w.category == "formatting" for w in verdict.warnings)

    async def test_evaluate_normal_body_passes_deterministic_checks(self) -> None:
        qg = QualityGate(llm=_make_llm_mock())
        comp = MagicMock(spec=CompositionResult)
        comp.body = "A" * 100
        comp.title = "Test Post"
        comp.hook = "Amazing hook!"
        comp.call_to_action = "Share now"
        comp.hashtags = ["#AI"]
        comp.has_code_blocks = False
        verdict = await qg.evaluate(comp)
        assert len(verdict.warnings) == 0
