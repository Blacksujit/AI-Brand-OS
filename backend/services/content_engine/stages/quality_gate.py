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
from services.prompt import PromptService

logger = get_logger(__name__)


class QualityGate:
    """Validates generated content quality before presenting to the user."""

    def __init__(self, llm: LLMClient, prompt_service: PromptService | None = None) -> None:
        self._llm = llm
        self._prompt_service = prompt_service or PromptService()

    async def evaluate(
        self,
        result: CompositionResult,
        context: AggregatedContext | None = None,
        model: str = "gemini-2.0-flash",
    ) -> QualityVerdict:
        platform = "LinkedIn" if not result.hashtags else "social media"

        system_prompt, user_prompt = self._prompt_service.build_prompt(
            "quality_gate",
            user_vars={
                "platform": platform,
                "title": result.title,
                "body": result.body,
                "hook": result.hook or "N/A",
                "call_to_action": result.call_to_action or "N/A",
                "expertise_areas": ", ".join(context.expertise_areas) if context and context.expertise_areas else "N/A",
            },
        )

        request = CompletionRequest(
            model=model,
            messages=[ChatMessage(role="user", content=user_prompt)],
            system_prompt=system_prompt,
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
