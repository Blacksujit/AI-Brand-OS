from __future__ import annotations

import json
from typing import Any

from core.llm import ChatMessage, CompletionRequest, LLMClient
from core.logging import get_logger
from services.content_engine.stages.models import (
    AggregatedContext,
    CompositionResult,
    QualityDimensions,
    QualityVerdict,
    QualityWarning,
)

logger = get_logger(__name__)

QUALITY_SYSTEM_PROMPT = """You are a content quality reviewer. Evaluate the given post across these dimensions:
1. factual_accuracy (0.0-1.0): Are claims supported? Any factual errors?
2. hallucination_risk (0.0-1.0): Does it make unsupported claims or fabricate information?
3. readability (0.0-1.0): Is it clear, well-structured, easy to read?
4. authenticity (0.0-1.0): Does it sound like a real person wrote it?
5. technical_depth (0.0-1.0): Is the depth appropriate for the topic?
6. engagement_potential (0.0-1.0): Would this stop a scroller?
7. platform_appropriateness (0.0-1.0): Right format for the platform?

Return JSON:
{
  "overall_score": 0.0-1.0,
  "verdict": "pass|warn|fail",
  "dimensions": { ... },
  "warnings": [{"severity": "critical|major|minor", "category": "...", "message": "...", "suggestion": "..."}],
  "recommendations": ["...", "..."]
}"""


class QualityGate:
    """Validates generated content quality before presenting to the user."""

    def __init__(self, llm: LLMClient) -> None:
        self._llm = llm

    async def evaluate(
        self,
        result: CompositionResult,
        context: AggregatedContext | None = None,
        model: str = "gemini-2.0-flash",
    ) -> QualityVerdict:
        user_prompt = (
            f"Evaluate this {'LinkedIn' if not result.hashtags else 'social media'} post:\n\n"
        )
        user_prompt += f"Title: {result.title}\n\n"
        user_prompt += f"Body:\n{result.body}\n\n"
        if result.hook:
            user_prompt += f"Hook: {result.hook}\n"
        if result.call_to_action:
            user_prompt += f"CTA: {result.call_to_action}\n"
        if context and context.expertise_areas:
            user_prompt += f"\nAuthor expertise: {', '.join(context.expertise_areas)}"

        request = CompletionRequest(
            model=model,
            messages=[ChatMessage(role="user", content=user_prompt)],
            system_prompt=QUALITY_SYSTEM_PROMPT,
            temperature=0.2,
            max_tokens=1024,
            response_format="json_object",
        )

        response = await self._llm.complete(request)
        data = self._parse_response(response.content)

        verdict = QualityVerdict(
            overall_score=data.get("overall_score", 0.5),
            verdict=data.get("verdict", "fail"),
            dimensions=QualityDimensions(**data.get("dimensions", {})),
            warnings=[QualityWarning(**w) for w in data.get("warnings", [])],
            recommendations=data.get("recommendations", []),
        )

        # Deterministic overrides
        if len(result.body) < 50:
            verdict.verdict = "fail"
            verdict.warnings.append(
                QualityWarning(
                    severity="critical",
                    category="length",
                    message="Post body is too short (< 50 characters)",
                )
            )
        if result.has_code_blocks and not result.body.count("```") >= 2:
            verdict.verdict = "warn"
            verdict.warnings.append(
                QualityWarning(
                    severity="major",
                    category="formatting",
                    message="Code block markers appear incomplete",
                )
            )

        logger.info(
            "quality_gate_result",
            overall_score=verdict.overall_score,
            verdict=verdict.verdict,
            warnings=len(verdict.warnings),
        )
        return verdict

    def _parse_response(self, content: str) -> dict[str, Any]:
        raw = content.strip()
        if raw.startswith("```"):
            raw = raw.strip("`").strip()
            if raw.startswith("json"):
                raw = raw[4:].strip()
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            logger.warning("quality_gate_parse_failed", raw=raw[:200])
            return {
                "overall_score": 0.5,
                "verdict": "warn",
                "dimensions": {},
                "warnings": [],
                "recommendations": [],
            }
