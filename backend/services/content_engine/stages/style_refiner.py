from __future__ import annotations

from core.logging import get_logger
from services.content_engine.stages.models import (
    CompositionResult,
    RefinementResult,
    StyleChange,
)

logger = get_logger(__name__)

# Common AI clichés to replace
AI_CLICHES = {
    "delve into": "explore",
    "let's dive in": "let's get started",
    "it's worth noting": "",
    "in today's digital landscape": "",
    "game-changer": "transformative",
    "in the world of": "in",
    "landscape": "field",
    "revolutionize": "change",
    "leverage": "use",
    "utilize": "use",
    "facilitate": "help",
    "unprecedented": "remarkable",
    "cutting-edge": "advanced",
    "ever-evolving": "changing",
    "shall": "will",
}


class StyleRefiner:
    """Applies style refinements to generated drafts.

    Deterministic — no LLM calls. Pattern-based transformation.
    """

    def __init__(self) -> None:
        self._style_service = None

    def wire(self, style_service: object | None = None) -> None:
        self._style_service = style_service

    async def refine(self, result: CompositionResult) -> RefinementResult:
        original = result.body
        refined = original

        changes: list[StyleChange] = []

        for cliche, replacement in AI_CLICHES.items():
            if cliche in refined.lower():
                count = refined.lower().count(cliche)
                if replacement:
                    refined = refined.lower().replace(cliche, replacement)
                    for _ in range(count):
                        changes.append(
                            StyleChange(
                                change_type="vocabulary_replacement",
                                original=cliche,
                                refined=replacement,
                                reason=f"Replaced AI cliché '{cliche}' with more natural wording",
                            )
                        )
                else:
                    refined = refined.lower().replace(cliche, "")
                    for _ in range(count):
                        changes.append(
                            StyleChange(
                                change_type="vocabulary_replacement",
                                original=cliche,
                                refined="(removed)",
                                reason=f"Removed filler phrase '{cliche}'",
                            )
                        )

        if result.hook and not refined.startswith(result.hook):
            refined = f"{result.hook}\n\n{refined}"
            changes.append(
                StyleChange(
                    change_type="hook_insertion",
                    original="",
                    refined=result.hook,
                    reason="Ensured hook is at the start of the body",
                )
            )

        score = max(0.0, 1.0 - len(changes) * 0.05)
        score = min(1.0, score)

        return RefinementResult(
            original_body=original,
            refined_body=refined,
            changes_applied=changes,
            style_adherence_score=score,
        )

    async def refine_full(self, result: CompositionResult) -> RefinementResult:
        return await self.refine(result)
