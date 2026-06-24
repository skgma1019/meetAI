"""Read all nonverbal JSON clips and extract biomechanical features into a CSV."""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.analyzers.nonverbal.extractor import FEATURE_NAMES, extract_clip_features, frames_from_annotation


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare nonverbal feature CSV from raw JSON labels.")
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument(
        "--output-csv",
        type=Path,
        default=REPO_ROOT / "data" / "processed" / "nonverbal_features.csv",
    )
    return parser.parse_args()


def infer_split(path: Path) -> str:
    text = path.as_posix().lower()
    if "training" in text:
        return "train"
    if "validation" in text:
        return "validation"
    return "unknown"


def infer_label(path: Path) -> str | None:
    match = re.search(r"(B\d{2})", path.name)
    return match.group(1) if match else None


def load_json(path: Path) -> dict:
    for enc in ("utf-8-sig", "utf-8", "cp949"):
        try:
            return json.loads(path.read_text(encoding=enc))
        except Exception:
            continue
    return {}


def process_file(path: Path) -> dict | None:
    label = infer_label(path)
    if not label:
        return None

    payload = load_json(path)
    annotation = payload.get("annotation", [])
    frames = frames_from_annotation(annotation)
    if not frames:
        return None

    features = extract_clip_features(frames)
    return {
        "split": infer_split(path),
        "file_id": path.stem,
        "label": label,
        **{name: round(features[name], 8) for name in FEATURE_NAMES},
    }


def main() -> None:
    args = parse_args()
    repo_root: Path = args.repo_root.resolve()

    label_roots = [
        repo_root / "public_speaking_training_labels",
        repo_root / "public_speaking_validation_labels",
    ]

    json_files: list[Path] = []
    for root in label_roots:
        if not root.exists():
            continue
        for path in root.rglob("*.json"):
            if "presentation" not in path.name and re.search(r"B\d{2}", path.name):
                json_files.append(path)

    json_files.sort()
    total = len(json_files)
    print(f"Found {total} nonverbal clip files.")

    rows: list[dict] = []
    for i, path in enumerate(json_files):
        if i % 2000 == 0:
            print(f"  processing {i}/{total}...")
        row = process_file(path)
        if row:
            rows.append(row)

    if not rows:
        print("No rows extracted.")
        return

    output: Path = args.output_csv
    output.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys())
    with output.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    from collections import Counter
    label_dist = Counter(r["label"] for r in rows)
    split_dist = Counter(r["split"] for r in rows)
    print(f"Wrote {len(rows)} rows to {output}")
    print(f"Split distribution: {dict(split_dist)}")
    print(f"Label distribution: {dict(sorted(label_dist.items()))}")


if __name__ == "__main__":
    main()
