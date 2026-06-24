from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any


LABELS: list[str] = ["B01", "B02", "B03", "B04", "B05", "B06", "B07", "B08", "B09", "B10", "B11", "B12"]

LABEL_NAMES: dict[str, str] = {
    "B01": "손동작(머리)",
    "B02": "손동작(얼굴)",
    "B03": "손동작(몸긁기)",
    "B04": "손동작(손톱)",
    "B05": "머리동작(고개흔들기)",
    "B06": "머리동작(좌우흔들기)",
    "B07": "머리동작(숙이기)",
    "B08": "팔동작(뒷짐)",
    "B09": "팔동작(무의미반동)",
    "B10": "자세(좌우흔들기)",
    "B11": "자세(비스듬히)",
    "B12": "자세(비비꼬기)",
}


def _safe_float(v: Any, default: float = 0.0) -> float:
    if v in (None, "", "None"):
        return default
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def _dot(w: list[float], x: list[float]) -> float:
    return sum(wi * xi for wi, xi in zip(w, x))


def _softmax(logits: list[float]) -> list[float]:
    max_l = max(logits)
    exps = [math.exp(l - max_l) for l in logits]
    total = sum(exps)
    return [e / total for e in exps]


class NonverbalClassifier:
    def __init__(self, payload: dict[str, Any]) -> None:
        self.feature_names: list[str] = payload["feature_names"]
        self.feature_stats: dict[str, dict[str, float]] = payload["feature_stats"]
        self.labels: list[str] = payload["labels"]
        # weights shape: [n_classes, n_features]
        self.weights: list[list[float]] = payload["weights"]
        self.biases: list[float] = payload["biases"]
        self.metrics: dict[str, Any] = payload.get("metrics", {})

    @classmethod
    def load(cls, path: str | Path) -> "NonverbalClassifier":
        return cls(json.loads(Path(path).read_text(encoding="utf-8")))

    def _normalize(self, feature_dict: dict[str, float]) -> list[float]:
        vector: list[float] = []
        for name in self.feature_names:
            raw = _safe_float(feature_dict.get(name))
            stats = self.feature_stats.get(name, {"mean": 0.0, "std": 1.0})
            std = stats["std"] if stats["std"] > 0 else 1.0
            vector.append((raw - stats["mean"]) / std)
        return vector

    def predict_proba(self, feature_dict: dict[str, float]) -> dict[str, float]:
        x = self._normalize(feature_dict)
        logits = [_dot(self.weights[i], x) + self.biases[i] for i in range(len(self.labels))]
        probs = _softmax(logits)
        return {label: round(p, 6) for label, p in zip(self.labels, probs)}

    def predict_label(self, feature_dict: dict[str, float]) -> str:
        proba = self.predict_proba(feature_dict)
        return max(proba, key=lambda k: proba[k])
