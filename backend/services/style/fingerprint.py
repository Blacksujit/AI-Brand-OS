from __future__ import annotations

from dataclasses import dataclass

from services.style.ema_signal import EMASignalProcessor


@dataclass
class FingerprintMetrics:
    lexical_richness_avg: float = 0.0
    avg_sentence_length_avg: float = 20.0
    formality_avg: float = 0.5
    humor_frequency_avg: float = 0.3
    analogy_frequency_avg: float = 0.3
    hook_rate: float = 0.0
    cta_rate: float = 0.0
    unique_word_ratio_avg: float = 0.5
    avg_word_length_avg: float = 5.0
    long_sentence_ratio_avg: float = 0.15
    signal_count: int = 0


class StyleFingerprint:
    MIN_SIGNALS = 5
    STABLE_SIGNALS = 50
    STABLE_CONFIDENCE = 0.85

    def __init__(self) -> None:
        self._ema = EMASignalProcessor()

    def compute_fingerprint(
        self,
        signals: list[dict],
        learning_rate: float | None = None,
    ) -> FingerprintMetrics:
        if not signals:
            return FingerprintMetrics()
        sorted_signals = sorted(signals, key=lambda s: s.get("_timestamp", 0))
        metrics = FingerprintMetrics()
        count = 0
        for signal in sorted_signals:
            alpha = learning_rate or self._compute_dynamic_alpha(count)
            self._ema = EMASignalProcessor(learning_rate=alpha)
            metrics = self._apply_signal_to_metrics(metrics, signal, alpha)
            count += 1
        metrics.signal_count = count
        return metrics

    def compute_fingerprint_from_accumulator(
        self,
        current: FingerprintMetrics,
        new_signals: list[dict],
        learning_rate: float | None = None,
    ) -> FingerprintMetrics:
        metrics = current
        count = current.signal_count
        for signal in new_signals:
            alpha = learning_rate or self._compute_dynamic_alpha(count)
            self._ema = EMASignalProcessor(learning_rate=alpha)
            metrics = self._apply_signal_to_metrics(metrics, signal, alpha)
            count += 1
        metrics.signal_count = count
        return metrics

    @staticmethod
    def _compute_dynamic_alpha(count: int) -> float:
        if count < 5:
            return 0.3
        if count < 20:
            return 0.15
        if count < 50:
            return 0.08
        return 0.05

    def _apply_signal_to_metrics(
        self,
        metrics: FingerprintMetrics,
        signal: dict,
        alpha: float,
    ) -> FingerprintMetrics:
        self._ema = EMASignalProcessor(learning_rate=alpha)
        ema = self._ema.update_ema
        metrics.lexical_richness_avg = ema(
            {"v": metrics.lexical_richness_avg},
            {"v": signal.get("vocabulary_richness", 0.0)},
        )["v"]
        metrics.avg_sentence_length_avg = ema(
            {"v": metrics.avg_sentence_length_avg},
            {"v": signal.get("avg_sentence_length", 20.0)},
        )["v"]
        metrics.formality_avg = ema(
            {"v": metrics.formality_avg},
            {"v": signal.get("formality_score", 0.5)},
        )["v"]
        metrics.humor_frequency_avg = ema(
            {"v": metrics.humor_frequency_avg},
            {"v": signal.get("humor_frequency", 0.3)},
        )["v"]
        metrics.analogy_frequency_avg = ema(
            {"v": metrics.analogy_frequency_avg},
            {"v": signal.get("analogy_frequency", 0.3)},
        )["v"]
        metrics.unique_word_ratio_avg = ema(
            {"v": metrics.unique_word_ratio_avg},
            {"v": signal.get("unique_word_ratio", 0.5)},
        )["v"]
        metrics.avg_word_length_avg = ema(
            {"v": metrics.avg_word_length_avg},
            {"v": signal.get("avg_word_length", 5.0)},
        )["v"]
        metrics.long_sentence_ratio_avg = ema(
            {"v": metrics.long_sentence_ratio_avg},
            {"v": signal.get("long_sentence_ratio", 0.15)},
        )["v"]
        return metrics

    def is_stable(
        self,
        signal_count: int,
        confidence: float,
    ) -> bool:
        if signal_count < self.MIN_SIGNALS:
            return False
        if signal_count >= self.STABLE_SIGNALS:
            return True
        return confidence >= self.STABLE_CONFIDENCE

    def compute_profile_params(
        self,
        metrics: FingerprintMetrics,
    ) -> dict:
        return {
            "avg_sentence_length": round(metrics.avg_sentence_length_avg, 2),
            "formality": round(metrics.formality_avg, 2),
            "humor_frequency": round(metrics.humor_frequency_avg, 2),
            "analogy_frequency": round(metrics.analogy_frequency_avg, 2),
            "sentence_variety": round(1.0 - metrics.long_sentence_ratio_avg, 2),
            "vocabulary_richness": round(metrics.lexical_richness_avg, 2),
            "technical_depth": round(0.3 + metrics.avg_word_length_avg * 0.1, 2),
            "passive_voice_frequency": round(1.0 - metrics.unique_word_ratio_avg, 2),
        }

    @staticmethod
    def fingerprint_similarity(
        params_a: dict,
        params_b: dict,
    ) -> float:
        shared_keys = set(params_a) & set(params_b)
        if not shared_keys:
            return 0.0
        distances = []
        for key in shared_keys:
            a_val = params_a[key]
            b_val = params_b[key]
            if isinstance(a_val, (int, float)) and isinstance(b_val, (int, float)):
                max_val = max(abs(a_val), abs(b_val), 1.0)
                distances.append(1.0 - min(abs(a_val - b_val) / max_val, 1.0))
        return sum(distances) / len(distances) if distances else 0.0
