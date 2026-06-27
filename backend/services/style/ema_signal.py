from __future__ import annotations


class EMASignalProcessor:
    def __init__(self, learning_rate: float = 0.1) -> None:
        self._alpha = learning_rate

    def update_ema(self, current: dict, new: dict) -> dict:
        alpha = self._alpha
        result = {}
        for key, new_val in new.items():
            if isinstance(new_val, (int, float)):
                old_val = current.get(key, new_val)
                result[key] = old_val * (1 - alpha) + new_val * alpha
            elif isinstance(new_val, list):
                result[key] = self._merge_lists(current.get(key, []), new_val, alpha)
            else:
                result[key] = new_val
        return result

    def update_ema_single(self, current: float, new: float) -> float:
        return current * (1 - self._alpha) + new * self._alpha

    def compute_confidence(self, signal_count: int, alpha: float | None = None) -> float:
        alpha = alpha or self._alpha
        effective_n = min(signal_count, 100)
        return 1.0 - (1.0 - alpha) ** effective_n

    def merge_signals(
        self,
        signals: list[dict],
        weights: list[float] | None = None,
    ) -> dict:
        if not signals:
            return {}
        if weights is None:
            weights = [1.0 / len(signals)] * len(signals)
        total_weight = sum(weights) or 1.0
        merged: dict = {}
        for signal, weight in zip(signals, weights, strict=False):
            normalized = weight / total_weight
            for key, val in signal.items():
                if isinstance(val, (int, float)):
                    merged[key] = merged.get(key, 0.0) + val * normalized
                elif isinstance(val, list):
                    prev = merged.get(key, [])
                    merged[key] = self._merge_into(prev, val, normalized)
                elif key not in merged:
                    merged[key] = val
        return merged

    @staticmethod
    def _merge_lists(current: list, new: list, alpha: float) -> list:
        if not new:
            return current
        old_set = set(current)
        for item in new:
            if item not in old_set:
                old_set.add(item)
        return list(old_set)

    @staticmethod
    def _merge_into(target: list, source: list, weight: float) -> list:
        if not source:
            return target
        existing = set(target)
        for item in source:
            if item not in existing:
                existing.add(item)
                target.append(item)
        return target
