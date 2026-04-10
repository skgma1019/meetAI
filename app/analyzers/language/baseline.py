from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any


GRADE_TO_SCORE = {
    "A+": 10.0,
    "A": 9.0,
    "A0": 9.0,
    "B+": 8.0,
    "B": 7.0,
    "B0": 7.0,
    "C+": 6.0,
    "C": 5.0,
    "C0": 5.0,
    "D+": 4.0,
    "D": 3.0,
    "D0": 3.0,
    "F": 1.0,
}
CANONICAL_GRADE_SCORES = sorted(set(GRADE_TO_SCORE.values()))


def _safe_float(value: Any, default: float = 0.0) -> float:
    if value in (None, "", "None"):
        return default
    return float(value)


@dataclass
class FeatureVector:
    values: list[float]
    feature_names: list[str]


def build_feature_row(record: dict[str, Any]) -> dict[str, Any]:
    word_count = _safe_float(record.get("word_count"))
    audible_word_count = _safe_float(record.get("audible_word_count"))
    sentence_count = _safe_float(record.get("sentence_count"))
    syllable_count = _safe_float(record.get("syllable_count"))
    presentation_script_chars = _safe_float(record.get("presentation_script_chars"))
    stt_script_chars = _safe_float(record.get("stt_script_chars"))
    fil_tag_count = _safe_float(record.get("fil_tag_count"))
    rep_tag_count = _safe_float(record.get("rep_tag_count"))
    wr_tag_count = _safe_float(record.get("wr_tag_count"))
    repeat_count_mean = _safe_float(record.get("repeat_count_mean"))
    filler_count_mean = _safe_float(record.get("filler_count_mean"))
    pause_count_mean = _safe_float(record.get("pause_count_mean"))
    wrong_count_mean = _safe_float(record.get("wrong_count_mean"))
    voice_speed_mean = _safe_float(record.get("voice_speed_mean"))
    voice_quality_score_mean = _safe_float(record.get("voice_quality_score_mean"))
    expert_grade_score_mean = _safe_float(record.get("expert_grade_score_mean"))

    avg_words_per_sentence = word_count / sentence_count if sentence_count else 0.0
    syllables_per_word = syllable_count / word_count if word_count else 0.0
    audible_word_ratio = audible_word_count / word_count if word_count else 0.0
    stt_to_script_ratio = stt_script_chars / presentation_script_chars if presentation_script_chars else 0.0
    filler_per_100_words = filler_count_mean / word_count * 100 if word_count else 0.0
    repeat_per_100_words = repeat_count_mean / word_count * 100 if word_count else 0.0
    wrong_per_100_words = wrong_count_mean / word_count * 100 if word_count else 0.0
    pause_per_100_words = pause_count_mean / word_count * 100 if word_count else 0.0
    tagged_disfluency_per_100_words = (
        (fil_tag_count + rep_tag_count + wr_tag_count) / word_count * 100 if word_count else 0.0
    )

    return {
        "split": record.get("split", "unknown"),
        "file_id": record.get("file_id"),
        "speaker_age_flag": record.get("speaker_age_flag", "unknown"),
        "presentation_type": record.get("presentation_type", "unknown"),
        "presentation_difficulty": record.get("presentation_difficulty", "unknown"),
        "audience_flag": record.get("audience_flag", "unknown"),
        "word_count": round(word_count, 6),
        "audible_word_count": round(audible_word_count, 6),
        "sentence_count": round(sentence_count, 6),
        "syllable_count": round(syllable_count, 6),
        "presentation_script_chars": round(presentation_script_chars, 6),
        "stt_script_chars": round(stt_script_chars, 6),
        "fil_tag_count": round(fil_tag_count, 6),
        "rep_tag_count": round(rep_tag_count, 6),
        "wr_tag_count": round(wr_tag_count, 6),
        "repeat_count_mean": round(repeat_count_mean, 6),
        "filler_count_mean": round(filler_count_mean, 6),
        "pause_count_mean": round(pause_count_mean, 6),
        "wrong_count_mean": round(wrong_count_mean, 6),
        "voice_speed_mean": round(voice_speed_mean, 6),
        "voice_quality_score_mean": round(voice_quality_score_mean, 6),
        "avg_words_per_sentence": round(avg_words_per_sentence, 6),
        "syllables_per_word": round(syllables_per_word, 6),
        "audible_word_ratio": round(audible_word_ratio, 6),
        "stt_to_script_ratio": round(stt_to_script_ratio, 6),
        "filler_per_100_words": round(filler_per_100_words, 6),
        "repeat_per_100_words": round(repeat_per_100_words, 6),
        "wrong_per_100_words": round(wrong_per_100_words, 6),
        "pause_per_100_words": round(pause_per_100_words, 6),
        "tagged_disfluency_per_100_words": round(tagged_disfluency_per_100_words, 6),
        "target_grade_score": round(expert_grade_score_mean, 6),
    }


def _dot(left: list[float], right: list[float]) -> float:
    return sum(l * r for l, r in zip(left, right, strict=True))


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _mae(actual: list[float], predicted: list[float]) -> float:
    return _mean([abs(a - p) for a, p in zip(actual, predicted, strict=True)])


def _rmse(actual: list[float], predicted: list[float]) -> float:
    return math.sqrt(_mean([(a - p) ** 2 for a, p in zip(actual, predicted, strict=True)]))


def _r2(actual: list[float], predicted: list[float]) -> float:
    if not actual:
        return 0.0
    actual_mean = _mean(actual)
    total_sum_squares = sum((value - actual_mean) ** 2 for value in actual)
    if total_sum_squares == 0:
        return 1.0
    residual_sum_squares = sum((a - p) ** 2 for a, p in zip(actual, predicted, strict=True))
    return 1.0 - (residual_sum_squares / total_sum_squares)


def _within_tolerance_ratio(actual: list[float], predicted: list[float], tolerance: float) -> float:
    if not actual:
        return 0.0
    match_count = sum(1 for a, p in zip(actual, predicted, strict=True) if abs(a - p) <= tolerance)
    return match_count / len(actual)


def _score_to_grade_bucket(score: float) -> float:
    return min(CANONICAL_GRADE_SCORES, key=lambda candidate: (abs(candidate - score), -candidate))


def _grade_match_rate(actual: list[float], predicted: list[float]) -> float:
    if not actual:
        return 0.0
    match_count = sum(
        1
        for a, p in zip(actual, predicted, strict=True)
        if _score_to_grade_bucket(a) == _score_to_grade_bucket(p)
    )
    return match_count / len(actual)


class LanguageBaselineModel:
    def __init__(self, payload: dict[str, Any]) -> None:
        self.payload = payload
        self.numeric_features: list[str] = payload["numeric_features"]
        self.numeric_stats: dict[str, dict[str, float]] = payload["numeric_stats"]
        self.categorical_features: list[str] = payload["categorical_features"]
        self.category_maps: dict[str, list[str]] = payload["category_maps"]
        self.weights: list[float] = payload["weights"]
        self.bias: float = payload["bias"]
        self.target_min: float = payload.get("target_min", 1.0)
        self.target_max: float = payload.get("target_max", 10.0)

    @classmethod
    def load(cls, path: str | Path) -> "LanguageBaselineModel":
        return cls(json.loads(Path(path).read_text(encoding="utf-8")))

    def build_vector(self, feature_row: dict[str, Any]) -> FeatureVector:
        values: list[float] = []
        names: list[str] = []

        for feature_name in self.numeric_features:
            stats = self.numeric_stats[feature_name]
            value = _safe_float(feature_row.get(feature_name))
            std = stats["std"] if stats["std"] > 0 else 1.0
            values.append((value - stats["mean"]) / std)
            names.append(feature_name)

        for feature_name in self.categorical_features:
            current_value = str(feature_row.get(feature_name, "unknown"))
            for category in self.category_maps[feature_name]:
                values.append(1.0 if current_value == category else 0.0)
                names.append(f"{feature_name}={category}")

        return FeatureVector(values=values, feature_names=names)

    def predict_score(self, feature_row: dict[str, Any]) -> float:
        vector = self.build_vector(feature_row)
        raw_score = self.bias + _dot(self.weights, vector.values)
        return round(max(self.target_min, min(self.target_max, raw_score)), 4)


def train_language_baseline(
    rows: list[dict[str, Any]],
    *,
    numeric_features: list[str],
    categorical_features: list[str],
    target_field: str,
    learning_rate: float = 0.03,
    epochs: int = 800,
    l2_penalty: float = 0.0005,
) -> dict[str, Any]:
    train_rows = [row for row in rows if row["split"] == "train"]
    validation_rows = [row for row in rows if row["split"] == "validation"]
    if not train_rows:
        raise ValueError("No training rows available.")

    numeric_stats: dict[str, dict[str, float]] = {}
    for feature_name in numeric_features:
        values = [_safe_float(row.get(feature_name)) for row in train_rows]
        mean_value = _mean(values)
        variance = _mean([(value - mean_value) ** 2 for value in values])
        std_value = math.sqrt(variance) or 1.0
        numeric_stats[feature_name] = {"mean": mean_value, "std": std_value}

    category_maps: dict[str, list[str]] = {}
    for feature_name in categorical_features:
        categories = sorted({str(row.get(feature_name, "unknown")) for row in train_rows})
        category_maps[feature_name] = categories

    temp_model = LanguageBaselineModel(
        {
            "numeric_features": numeric_features,
            "numeric_stats": numeric_stats,
            "categorical_features": categorical_features,
            "category_maps": category_maps,
            "weights": [0.0]
            * (
                len(numeric_features)
                + sum(len(categories) for categories in category_maps.values())
            ),
            "bias": 0.0,
        }
    )

    x_train = [temp_model.build_vector(row).values for row in train_rows]
    y_train = [_safe_float(row[target_field]) for row in train_rows]
    feature_count = len(x_train[0])
    weights = [0.0] * feature_count
    bias = _mean(y_train)
    sample_count = len(x_train)

    for _ in range(epochs):
        grad_w = [0.0] * feature_count
        grad_b = 0.0
        for features, target in zip(x_train, y_train, strict=True):
            prediction = bias + _dot(weights, features)
            error = prediction - target
            grad_b += error
            for index, value in enumerate(features):
                grad_w[index] += error * value

        inv_n = 1.0 / sample_count
        grad_b *= inv_n
        for index in range(feature_count):
            grad_w[index] = grad_w[index] * inv_n + l2_penalty * weights[index]
            weights[index] -= learning_rate * grad_w[index]
        bias -= learning_rate * grad_b

    payload = {
        "numeric_features": numeric_features,
        "numeric_stats": numeric_stats,
        "categorical_features": categorical_features,
        "category_maps": category_maps,
        "weights": [round(weight, 8) for weight in weights],
        "bias": round(bias, 8),
        "target_min": min(y_train),
        "target_max": max(y_train),
    }
    model = LanguageBaselineModel(payload)

    def _predict_many(dataset_rows: list[dict[str, Any]]) -> list[float]:
        return [model.predict_score(row) for row in dataset_rows]

    train_predictions = _predict_many(train_rows)
    validation_predictions = _predict_many(validation_rows) if validation_rows else []
    train_actual = [_safe_float(row[target_field]) for row in train_rows]
    validation_actual = [_safe_float(row[target_field]) for row in validation_rows]

    metrics = {
        "train_count": len(train_rows),
        "validation_count": len(validation_rows),
        "train_mae": round(_mae(train_actual, train_predictions), 6),
        "train_rmse": round(_rmse(train_actual, train_predictions), 6),
        "train_r2": round(_r2(train_actual, train_predictions), 6),
        "train_within_0_5_ratio": round(_within_tolerance_ratio(train_actual, train_predictions, 0.5), 6),
        "train_grade_match_rate": round(_grade_match_rate(train_actual, train_predictions), 6),
        "validation_mae": round(_mae(validation_actual, validation_predictions), 6) if validation_rows else None,
        "validation_rmse": round(_rmse(validation_actual, validation_predictions), 6) if validation_rows else None,
        "validation_r2": round(_r2(validation_actual, validation_predictions), 6) if validation_rows else None,
        "validation_within_0_5_ratio": (
            round(_within_tolerance_ratio(validation_actual, validation_predictions, 0.5), 6)
            if validation_rows
            else None
        ),
        "validation_grade_match_rate": (
            round(_grade_match_rate(validation_actual, validation_predictions), 6) if validation_rows else None
        ),
    }

    payload["metrics"] = metrics
    return payload
