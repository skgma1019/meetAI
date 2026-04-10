from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.analyzers.language.baseline import build_feature_row


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a training-ready language feature table.")
    parser.add_argument(
        "--input-csv",
        type=Path,
        default=Path("data/processed/linguistic_manifest.csv"),
        help="Path to the linguistic manifest CSV.",
    )
    parser.add_argument(
        "--output-csv",
        type=Path,
        default=Path("data/processed/language_features.csv"),
        help="Path to the generated feature CSV.",
    )
    parser.add_argument(
        "--summary-json",
        type=Path,
        default=Path("data/processed/language_features_summary.json"),
        help="Path to the generated summary JSON.",
    )
    return parser.parse_args()


def load_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_rows(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys()) if rows else []
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    args = parse_args()
    rows = load_rows(args.input_csv)
    feature_rows = [build_feature_row(row) for row in rows]
    write_rows(args.output_csv, feature_rows)

    summary = {
        "input_csv": str(args.input_csv.resolve()),
        "output_csv": str(args.output_csv.resolve()),
        "row_count": len(feature_rows),
        "train_count": sum(1 for row in feature_rows if row["split"] == "train"),
        "validation_count": sum(1 for row in feature_rows if row["split"] == "validation"),
        "feature_columns": list(feature_rows[0].keys()) if feature_rows else [],
    }
    args.summary_json.parent.mkdir(parents=True, exist_ok=True)
    args.summary_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
