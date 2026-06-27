from __future__ import annotations

import pytest

from services.evaluation import EvaluationMetrics, EvaluationService


class TestEvaluationService:
    @pytest.mark.asyncio
    async def test_evaluate_text(self) -> None:
        service = EvaluationService()
        result = await service.evaluate_text(
            text="Artificial intelligence is transforming how brands connect with their audiences. "
            "By leveraging machine learning algorithms, marketers can personalize content at scale. "
            "This shift requires new thinking about creativity and data-driven decision making.",
            title="The Future of AI in Marketing",
        )
        assert isinstance(result, EvaluationMetrics)
        assert 0.0 <= result.overall_score <= 1.0
        assert 0.0 <= result.readability_score <= 1.0
        assert 0.0 <= result.engagement_score <= 1.0
        assert 0.0 <= result.authenticity_score <= 1.0
        assert 0.0 <= result.technical_depth_score <= 1.0
        assert isinstance(result.feedback, list)

    @pytest.mark.asyncio
    async def test_same_text_returns_same_score(self) -> None:
        service = EvaluationService()
        text = "Artificial intelligence is transforming how brands connect."
        first = await service.evaluate_text(text=text)
        second = await service.evaluate_text(text=text)
        assert first.overall_score == second.overall_score

    @pytest.mark.asyncio
    async def test_empty_body_returns_low_score(self) -> None:
        service = EvaluationService()
        result = await service.evaluate_text(text="", title="Test")
        assert result.technical_depth_score == 0.0
        assert result.overall_score < 0.6

    @pytest.mark.asyncio
    async def test_readability_scoring(self) -> None:
        service = EvaluationService()
        easy_text = "AI is changing marketing. Brands use data. Content gets personal."
        easy_result = await service.evaluate_text(text=easy_text, title="Test")
        complex_text = (
            "The synergistic implementation of artificial intelligence within "
            "contemporary marketing paradigms necessitates a comprehensive "
            "reconceptualization of traditional content dissemination strategies."
        )
        complex_result = await service.evaluate_text(text=complex_text, title="Test")
        assert easy_result.readability_score >= complex_result.readability_score

    @pytest.mark.asyncio
    async def test_authenticity_penalty(self) -> None:
        service = EvaluationService()
        cliche_text = (
            "In today's fast-paced digital landscape, it's more important than ever "
            "to think outside the box and leverage game-changing solutions."
        )
        result = await service.evaluate_text(text=cliche_text, title="Test")
        assert result.authenticity_score < 0.9

    @pytest.mark.asyncio
    async def test_technical_depth_with_code(self) -> None:
        service = EvaluationService()
        text_with_code = (
            "Here is a Python function:\n```python\ndef hello():\n    return 'world'\n```\n"
            "This shows how simple AI integration can be."
        )
        result = await service.evaluate_text(text=text_with_code, title="Test")
        assert result.technical_depth_score >= 0.5

    @pytest.mark.asyncio
    async def test_body_with_hooks(self) -> None:
        service = EvaluationService()
        body_with_hook = (
            "Most founders ignore this one metric.\n\n"
            "Here's the thing about retention curves nobody talks about.\n\n"
            "When you look at SaaS data, the pattern is clear: companies that "
            "focus on NPS-driven growth outperform their peers by 3x."
        )
        result = await service.evaluate_text(text=body_with_hook, title="Retention Secrets")
        assert result.overall_score > 0

    def test_wire(self) -> None:
        service = EvaluationService()
        fake_gate = object()
        service.wire(fake_gate)
        assert service._quality_gate is fake_gate

    def test_empty_text_returns_low_technical_depth(self) -> None:
        service = EvaluationService()
        import asyncio

        result = asyncio.run(service.evaluate_text(text=""))
        assert result.technical_depth_score == 0.0
