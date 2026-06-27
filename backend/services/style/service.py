from __future__ import annotations

import uuid

from loguru import logger

from database.db import Database
from models.style import StyleProfile, StyleRating, StyleSignal
from repositories.style import (
    StyleProfileRepository,
    StyleRatingRepository,
    StyleSignalRepository,
)
from schemas.style import StyleParams, StyleProfileResponse
from services.style.analyzers import StyleAnalyzer
from services.style.ema_signal import EMASignalProcessor
from services.style.fingerprint import FingerprintMetrics, StyleFingerprint


class StyleService:
    def __init__(
        self,
        db: Database,
        learning_rate: float = 0.1,
    ) -> None:
        self._db = db
        self._analyzer = StyleAnalyzer()
        self._ema = EMASignalProcessor(learning_rate=learning_rate)
        self._fingerprint = StyleFingerprint()

    async def get_profile(self, user_id: uuid.UUID) -> StyleProfileResponse:
        async with self._db.session() as session:
            repo = StyleProfileRepository(session)
            profile = await repo.get_by_user_id(user_id)
            if profile is None:
                profile = await repo.create(StyleProfile(user_id=user_id))
            signal_count = await StyleSignalRepository(session).count_by_profile(profile.id)
            is_stable = self._fingerprint.is_stable(signal_count, profile.confidence)
            params = profile.style_params or {}
            return StyleProfileResponse(
                id=str(profile.id),
                user_id=str(profile.user_id),
                style_params=StyleParams(**params),
                learning_rate=profile.learning_rate,
                confidence=round(profile.confidence, 4),
                total_ratings=profile.total_ratings,
                total_edits=profile.total_edits,
                total_approved=profile.total_approved,
                is_stable=is_stable,
            )

    async def update_profile(
        self,
        user_id: uuid.UUID,
        updates: dict,
    ) -> StyleProfileResponse:
        async with self._db.session() as session:
            repo = StyleProfileRepository(session)
            profile = await repo.get_by_user_id(user_id)
            if profile is None:
                profile = await repo.create(StyleProfile(user_id=user_id, **updates))
            else:
                profile = await repo.update(profile.id, updates)
                if profile is None:
                    msg = f"Profile {profile.id} not found after update"
                    raise ValueError(msg)
            signal_count = await StyleSignalRepository(session).count_by_profile(profile.id)
            is_stable = self._fingerprint.is_stable(signal_count, profile.confidence)
            params = profile.style_params or {}
            return StyleProfileResponse(
                id=str(profile.id),
                user_id=str(profile.user_id),
                style_params=StyleParams(**params),
                learning_rate=profile.learning_rate,
                confidence=round(profile.confidence, 4),
                total_ratings=profile.total_ratings,
                total_edits=profile.total_edits,
                total_approved=profile.total_approved,
                is_stable=is_stable,
            )

    async def analyze(
        self,
        user_id: uuid.UUID,
        text: str,
    ) -> dict:
        async with self._db.session() as session:
            repo = StyleProfileRepository(session)
            profile = await repo.get_by_user_id(user_id)
        params = (
            StyleParams(**profile.style_params)
            if profile and profile.style_params
            else StyleParams()
        )
        analysis = self._analyzer.analyze(text, params)
        deviations = self._compute_deviations(analysis, params)
        return {
            "vocabulary_match": round(analysis.get("lexical_score", 0.0) * 100, 2),
            "sentence_structure_match": round(analysis.get("syntactic_score", 0.0) * 100, 2),
            "tone_alignment": round(analysis.get("tonal_score", 0.0) * 100, 2),
            "technical_depth_match": round(analysis.get("lexical_score", 0.0) * 100, 2),
            "overall_similarity": round(analysis.get("overall", 0.0) * 100, 2),
            "deviations": deviations,
        }

    async def import_content(
        self,
        user_id: uuid.UUID,
        texts: list[str],
    ) -> dict:
        async with self._db.session() as session:
            profile_repo = StyleProfileRepository(session)
            signal_repo = StyleSignalRepository(session)
            profile = await profile_repo.get_by_user_id(user_id)
            if profile is None:
                profile = await profile_repo.create(StyleProfile(user_id=user_id))
            signals_created = 0
            for text in texts:
                signal_data = self._analyzer.extract_signal_data(text)
                signal = StyleSignal(
                    profile_id=profile.id,
                    signal_type="import",
                    signal_data=signal_data,
                    weight=1.0,
                )
                await signal_repo.add(signal)
                signals_created += 1
            signal_count = await signal_repo.count_by_profile(profile.id)
            confidence = self._ema.compute_confidence(signal_count)
            await profile_repo.update(
                profile.id,
                {
                    "confidence": confidence,
                    "total_ratings": profile.total_ratings,
                },
            )
            await session.commit()
        if signal_count >= StyleFingerprint.MIN_SIGNALS:
            await self._reconverge_fingerprint(profile.id)
        return {
            "signals_created": signals_created,
            "profile_confidence": round(confidence, 4),
        }

    async def rate_draft(
        self,
        user_id: uuid.UUID,
        draft_id: str,
        score: int,
        comment: str | None = None,
        dimension_scores: dict | None = None,
    ) -> StyleProfileResponse:
        async with self._db.session() as session:
            rating_repo = StyleRatingRepository(session)
            profile_repo = StyleProfileRepository(session)
            signal_repo = StyleSignalRepository(session)
            rating = StyleRating(
                user_id=user_id,
                draft_id=draft_id,
                score=score,
                comment=comment,
                dimension_scores=dimension_scores,
            )
            await rating_repo.add(rating)
            profile = await profile_repo.get_by_user_id(user_id)
            if profile is None:
                profile = await profile_repo.create(StyleProfile(user_id=user_id))
            new_total = profile.total_ratings + 1
            new_confidence = self._ema.compute_confidence(new_total)
            await profile_repo.update(
                profile.id,
                {
                    "total_ratings": new_total,
                    "confidence": new_confidence,
                },
            )
            await session.commit()
            signal_count = await signal_repo.count_by_profile(profile.id)
            is_stable = self._fingerprint.is_stable(signal_count, profile.confidence)
            params = profile.style_params or {}
            return StyleProfileResponse(
                id=str(profile.id),
                user_id=str(profile.user_id),
                style_params=StyleParams(**params),
                learning_rate=profile.learning_rate,
                confidence=round(profile.confidence, 4),
                total_ratings=new_total,
                total_edits=profile.total_edits,
                total_approved=profile.total_approved,
                is_stable=is_stable,
            )

    async def get_insights(self, user_id: uuid.UUID) -> dict:
        async with self._db.session() as session:
            profile_repo = StyleProfileRepository(session)
            signal_repo = StyleSignalRepository(session)
            profile = await profile_repo.get_by_user_id(user_id)
            if profile is None:
                return self._empty_insights()
            signal_count = await signal_repo.count_by_profile(profile.id)
            is_stable = self._fingerprint.is_stable(signal_count, profile.confidence)
            signals = await signal_repo.list_recent(profile.id)
        metrics = self._fingerprint.compute_fingerprint(
            [s.signal_data or {} for s in signals if s.signal_data]
        )
        return {
            "signals_collected": signal_count,
            "signals_needed_for_stable": StyleFingerprint.STABLE_SIGNALS,
            "profile_confidence": round(profile.confidence, 4),
            "is_stable": is_stable,
            "days_until_stable_estimate": (
                max(1, (StyleFingerprint.STABLE_SIGNALS - signal_count) // 2)
                if not is_stable
                else None
            ),
            "insights": self._compute_insight_items(metrics),
        }

    async def get_learning_progress(
        self,
        user_id: uuid.UUID,
    ) -> dict:
        async with self._db.session() as session:
            profile_repo = StyleProfileRepository(session)
            signal_repo = StyleSignalRepository(session)
            profile = await profile_repo.get_by_user_id(user_id)
            if profile is None:
                return {
                    "signals_collected": 0,
                    "profile_confidence": 0.0,
                    "is_stable": False,
                }
            signal_count = await signal_repo.count_by_profile(profile.id)
            return {
                "signals_collected": signal_count,
                "profile_confidence": round(profile.confidence, 4),
                "is_stable": self._fingerprint.is_stable(signal_count, profile.confidence),
                "total_ratings": profile.total_ratings,
                "total_edits": profile.total_edits,
                "total_approved": profile.total_approved,
            }

    async def _reconverge_fingerprint(
        self,
        profile_id: uuid.UUID,
    ) -> None:
        async with self._db.session() as session:
            signal_repo = StyleSignalRepository(session)
            signals = await signal_repo.list_recent(profile_id, limit=100)
        signal_data_list = [s.signal_data or {} for s in signals if s.signal_data]
        if not signal_data_list:
            return
        self._fingerprint.compute_fingerprint(signal_data_list)
        logger.info(
            "Reconverged fingerprint for profile {} with {} signals",
            profile_id,
            len(signal_data_list),
        )

    @staticmethod
    def _compute_deviations(analysis: dict, params: StyleParams) -> list[str]:
        deviations = []
        if analysis.get("tonal_score", 1.0) < 0.6:
            deviations.append("tone")
        if analysis.get("syntactic_score", 1.0) < 0.6:
            deviations.append("sentence_structure")
        if analysis.get("lexical_score", 1.0) < 0.6:
            deviations.append("vocabulary")
        if analysis.get("structural_score", 1.0) < 0.6:
            deviations.append("structure")
        return deviations

    @staticmethod
    def _empty_insights() -> dict:
        return {
            "signals_collected": 0,
            "signals_needed_for_stable": StyleFingerprint.STABLE_SIGNALS,
            "profile_confidence": 0.0,
            "is_stable": False,
            "days_until_stable_estimate": None,
            "insights": [],
        }

    @staticmethod
    def _compute_insight_items(metrics: FingerprintMetrics) -> list[dict]:
        items = []
        items.append(
            {
                "dimension": "Formality",
                "value": round(metrics.formality_avg * 100, 1),
                "trend": "stable",
            }
        )
        items.append(
            {
                "dimension": "Sentence Length",
                "value": round(metrics.avg_sentence_length_avg, 1),
                "trend": "stable",
            }
        )
        items.append(
            {
                "dimension": "Vocabulary Richness",
                "value": round(metrics.lexical_richness_avg, 2),
                "trend": "stable",
            }
        )
        items.append(
            {
                "dimension": "Humor Frequency",
                "value": round(metrics.humor_frequency_avg, 2),
                "trend": "stable",
            }
        )
        items.append(
            {
                "dimension": "Analogy Usage",
                "value": round(metrics.analogy_frequency_avg, 2),
                "trend": "stable",
            }
        )
        return items
