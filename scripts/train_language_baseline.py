from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.analyzers.language.baseline import train_language_baseline


NUMERIC_FEATURES = [
    "word_count",
    "audible_word_count",
    "sentence_count",
    "syllable_count",
    "fil_tag_count",
    "rep_tag_count",
    "wr_tag_count",
    "repeat_count_mean",
    "filler_count_mean",
    "pause_count_mean",
    "wrong_count_mean",
    "voice_speed_mean",
    "voice_quality_score_mean",
    "avg_words_per_sentence",
    "syllables_per_word",
    "audible_word_ratio",
    "stt_to_script_ratio",
    "filler_per_100_words",
    "repeat_per_100_words",
    "wrong_per_100_words",
    "pause_per_100_words",
    "tagged_disfluency_per_100_words",
]

CATEGORICAL_FEATURES = [
    "speaker_age_flag",
    "presentation_type",
    "presentation_difficulty",
    "audience_flag",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train a simple language baseline model from prepared features.")
    parser.add_argument(
        "--input-csv",
        type=Path,
        default=Path("data/processed/language_features.csv"),
        help="Path to the prepared feature CSV.",
    )
    parser.add_argument(
        "--output-model",
        type=Path,
        default=Path("outputs/checkpoints/language_baseline.json"),
        help="Path to save the trained baseline model.",
    )
    parser.add_argument(
        "--epochs",
        type=int,
        default=900,
        help="Number of gradient descent epochs.",
    )
    parser.add_argument(
        "--learning-rate",
        type=float,
        default=0.03,
        help="Gradient descent learning rate.",
    )
    parser.add_argument(
        "--l2-penalty",
        type=float,
        default=0.0005,
        help="L2 regularization strength.",
    )
    return parser.parse_args()


def load_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def main() -> None:
    args = parse_args()
    rows = load_rows(args.input_csv)
    model_payload = train_language_baseline(
        rows,
        numeric_features=NUMERIC_FEATURES,
        categorical_features=CATEGORICAL_FEATURES,
        target_field="target_grade_score",
        learning_rate=args.learning_rate,
        epochs=args.epochs,
        l2_penalty=args.l2_penalty,
    )
    args.output_model.parent.mkdir(parents=True, exist_ok=True)
    args.output_model.write_text(json.dumps(model_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(model_payload["metrics"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
