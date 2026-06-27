from __future__ import annotations

from typing import Any

from core.logging import get_logger

logger = get_logger(__name__)


class EvaluationMetrics:
    """Quality evaluation metrics for generated content."""

    def __init__(
        self,
        overall_score: float = 0.0,
        readability_score: float = 0.0,
        engagement_score: float = 0.0,
        authenticity_score: float = 0.0,
        technical_depth_score: float = 0.0,
        feedback: list[str] | None = None,
    ) -> None:
        self.overall_score = overall_score
        self.readability_score = readability_score
        self.engagement_score = engagement_score
        self.authenticity_score = authenticity_score
        self.technical_depth_score = technical_depth_score
        self.feedback = feedback or []


class EvaluationService:
    """Evaluates content quality across multiple dimensions.

    Provides both LLM-based evaluation (via the QualityGate)
    and deterministic heuristic scoring.
    """

    def __init__(self) -> None:
        self._quality_gate = None

    def wire(self, quality_gate: object | None = None) -> None:
        self._quality_gate = quality_gate

    async def evaluate_text(self, text: str, title: str = "") -> EvaluationMetrics:
        scores = self._heuristic_scores(text)

        return EvaluationMetrics(
            overall_score=scores["overall"],
            readability_score=scores["readability"],
            engagement_score=scores["engagement"],
            authenticity_score=scores["authenticity"],
            technical_depth_score=scores["technical_depth"],
            feedback=scores.get("feedback", []),
        )

    def _heuristic_scores(self, text: str) -> dict[str, Any]:
        feedback: list[str] = []
        words = text.split()
        word_count = len(words)
        sentences = text.replace("!", ".").replace("?", ".").split(".")
        sentences = [s.strip() for s in sentences if s.strip()]
        sentence_count = max(1, len(sentences))
        avg_sentence_len = word_count / sentence_count

        readability = 0.7
        if avg_sentence_len > 30:
            readability = max(0.2, 0.7 - (avg_sentence_len - 30) * 0.01)
            feedback.append("Sentences are longer than average — consider shortening")
        elif avg_sentence_len < 8:
            readability = min(1.0, 0.7 + (8 - avg_sentence_len) * 0.02)
            feedback.append("Very short sentences — could add more detail")

        paragraphs = [p for p in text.split("\n\n") if p.strip()]
        if not paragraphs:
            engagement = 0.3
            feedback.append("No paragraph breaks — hard to read on mobile")
        elif len(paragraphs) >= 3:
            engagement = 0.8
        else:
            engagement = 0.6

        cliches = [
            "delve",
            "landscape",
            "revolutionize",
            "game-changer",
            "unprecedented",
            "cutting-edge",
            "leverage",
            "utilize",
        ]
        cliche_count = sum(1 for c in cliches if c.lower() in text.lower())
        authenticity = max(0.0, 0.9 - cliche_count * 0.1)
        if cliche_count > 2:
            feedback.append(f"Found {cliche_count} AI clichés — consider more natural language")

        if word_count > 0:
            has_code = "```" in text
            has_stats = any(c.isdigit() for c in text[:200])
            has_questions = "?" in text
            depth = 0.5
            if has_code:
                depth += 0.2
            if has_stats:
                depth += 0.1
            if has_questions:
                depth += 0.05
            technical_depth = min(1.0, depth)
        else:
            technical_depth = 0.0

        overall = round((readability + engagement + authenticity + technical_depth) / 4, 2)

        return {
            "overall": overall,
            "readability": round(readability, 2),
            "engagement": round(engagement, 2),
            "authenticity": round(authenticity, 2),
            "technical_depth": round(technical_depth, 2),
            "feedback": feedback,
        }
