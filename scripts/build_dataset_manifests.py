from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from pathlib import Path
from statistics import mean
from typing import Any


GRADE_TO_SCORE = {
    "A+": 10,
    "A": 9,
    "A0": 9,
    "B+": 8,
    "B": 7,
    "B0": 7,
    "C+": 6,
    "C": 5,
    "C0": 5,
    "D+": 4,
    "D": 3,
    "D0": 3,
    "F": 1,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build linguistic and nonverbal tabular manifests from the extracted public speaking dataset."
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Repository root that contains the extracted dataset directories.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Directory where generated manifest files will be written. Defaults to <repo-root>/data/processed.",
    )
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    encodings = ("utf-8-sig", "utf-8", "cp949")
    last_error: Exception | None = None
    for encoding in encodings:
        try:
            with path.open("r", encoding=encoding) as handle:
                return json.load(handle)
        except Exception as exc:  # noqa: BLE001
            last_error = exc
    raise RuntimeError(f"Failed to read JSON: {path}") from last_error


def safe_mean(values: list[float]) -> float | None:
    return round(mean(values), 6) if values else None


def text_len(value: Any) -> int:
    if not isinstance(value, str):
        return 0
    return len(value.strip())


def count_tag(text: str, tag_name: str) -> int:
    if not isinstance(text, str):
        return 0
    return len(re.findall(fr"<{tag_name}>", text))


def infer_split(path: Path) -> str:
    path_text = path.as_posix().lower()
    if "training" in path_text:
        return "train"
    if "validation" in path_text:
        return "validation"
    return "unknown"


def infer_nonverbal_label(path: Path) -> str | None:
    match = re.search(r"(B\d{2})", path.name)
    return match.group(1) if match else None


def evaluation_grade_summary(evaluations: list[dict[str, Any]]) -> tuple[str | None, float | None]:
    grades = [
        item.get("evaluation", {}).get("eval_grade")
        for item in evaluations
        if item.get("evaluation", {}).get("eval_grade")
    ]
    if not grades:
        return None, None

    mode_grade = Counter(grades).most_common(1)[0][0]
    numeric_scores = [GRADE_TO_SCORE[grade] for grade in grades if grade in GRADE_TO_SCORE]
    return mode_grade, safe_mean(numeric_scores)


def parse_linguistic_record(path: Path) -> dict[str, Any]:
    payload = load_json(path)

    speaker = payload.get("speaker", {})
    presentation = payload.get("presentation", {})
    script = payload.get("script", {})
    evaluations = payload.get("evaluations", [])

    grade_mode, grade_score_mean = evaluation_grade_summary(evaluations)

    repeat_cnts: list[float] = []
    repeat_scrs: list[float] = []
    filler_cnts: list[float] = []
    filler_scrs: list[float] = []
    pause_cnts: list[float] = []
    pause_scrs: list[float] = []
    wrong_cnts: list[float] = []
    wrong_scrs: list[float] = []
    voice_quality_scrs: list[float] = []
    voice_speed_values: list[float] = []
    voice_speed_scrs: list[float] = []

    for item in evaluations:
        repeat = item.get("repeat", {})
        filler_words = item.get("filler_words", {})
        pause = item.get("pause", {})
        wrong = item.get("wrong", {})
        voice_quality = item.get("voice_quality", {})
        voice_speed = item.get("voice_speed", {})

        if isinstance(repeat.get("repeat_cnt"), (int, float)):
            repeat_cnts.append(float(repeat["repeat_cnt"]))
        if isinstance(repeat.get("repeat_scr"), (int, float)):
            repeat_scrs.append(float(repeat["repeat_scr"]))
        if isinstance(filler_words.get("filler_words_cnt"), (int, float)):
            filler_cnts.append(float(filler_words["filler_words_cnt"]))
        if isinstance(filler_words.get("filler_words_scr"), (int, float)):
            filler_scrs.append(float(filler_words["filler_words_scr"]))
        if isinstance(pause.get("pause_cnt"), (int, float)):
            pause_cnts.append(float(pause["pause_cnt"]))
        if isinstance(pause.get("pause_scr"), (int, float)):
            pause_scrs.append(float(pause["pause_scr"]))
        if isinstance(wrong.get("wrong_cnt"), (int, float)):
            wrong_cnts.append(float(wrong["wrong_cnt"]))
        if isinstance(wrong.get("wrong_scr"), (int, float)):
            wrong_scrs.append(float(wrong["wrong_scr"]))
        if isinstance(voice_quality.get("voc_quality_scr"), (int, float)):
            voice_quality_scrs.append(float(voice_quality["voc_quality_scr"]))
        if isinstance(voice_speed.get("voc_speed"), (int, float)):
            voice_speed_values.append(float(voice_speed["voc_speed"]))
        if isinstance(voice_speed.get("voc_speed_sec_scr"), (int, float)):
            voice_speed_scrs.append(float(voice_speed["voc_speed_sec_scr"]))

    script_tag_text = script.get("script_tag_txt", "")
    file_id = path.stem.replace("_presentation", "")

    return {
        "record_type": "linguistic",
        "split": infer_split(path),
        "source_file": str(path),
        "file_id": file_id,
        "category_folder": path.parent.name,
        "speaker_age_flag": speaker.get("age_flag"),
        "speaker_gender": speaker.get("gender"),
        "speaker_job": speaker.get("job"),
        "audience_flag": speaker.get("aud_flag"),
        "presentation_topic": presentation.get("presen_topic"),
        "presentation_type": presentation.get("presen_type"),
        "presentation_location": presentation.get("presen_location"),
        "presentation_difficulty": presentation.get("presen_difficulty"),
        "start_time": script.get("start_time"),
        "end_time": script.get("end_time"),
        "syllable_count": script.get("syllable_cnt"),
        "word_count": script.get("word_cnt"),
        "audible_word_count": script.get("audible_word_cnt"),
        "sentence_count": script.get("sent_cnt"),
        "presentation_script_chars": text_len(presentation.get("presen_script")),
        "stt_script_chars": text_len(script.get("script_stt_txt")),
        "tagged_script_chars": text_len(script_tag_text),
        "wr_tag_count": count_tag(script_tag_text, "WR"),
        "fil_tag_count": count_tag(script_tag_text, "FIL"),
        "rep_tag_count": count_tag(script_tag_text, "REP"),
        "evaluation_count": len(evaluations),
        "expert_grade_mode": grade_mode,
        "expert_grade_score_mean": grade_score_mean,
        "repeat_count_mean": safe_mean(repeat_cnts),
        "repeat_score_mean": safe_mean(repeat_scrs),
        "filler_count_mean": safe_mean(filler_cnts),
        "filler_score_mean": safe_mean(filler_scrs),
        "pause_count_mean": safe_mean(pause_cnts),
        "pause_score_mean": safe_mean(pause_scrs),
        "wrong_count_mean": safe_mean(wrong_cnts),
        "wrong_score_mean": safe_mean(wrong_scrs),
        "voice_quality_score_mean": safe_mean(voice_quality_scrs),
        "voice_speed_mean": safe_mean(voice_speed_values),
        "voice_speed_score_mean": safe_mean(voice_speed_scrs),
    }


def parse_nonverbal_record(path: Path) -> dict[str, Any]:
    payload = load_json(path)
    dataset = payload.get("dataset", {})
    annotations = payload.get("annotation", [])

    frame_counts: list[float] = []
    keypoint_counts: list[float] = []

    for item in annotations:
        frame_count = item.get("frame_count")
        if isinstance(frame_count, (int, float)):
            frame_counts.append(float(frame_count))

        keypoints = item.get("keypoints", [])
        if isinstance(keypoints, list):
            keypoint_counts.append(float(len(keypoints)))

    return {
        "record_type": "nonverbal",
        "split": infer_split(path),
        "source_file": str(path),
        "file_id": path.stem,
        "category_folder": path.parent.name,
        "dataset_id": dataset.get("id"),
        "dataset_name": dataset.get("name"),
        "duration_seconds": dataset.get("duration"),
        "resolution": dataset.get("resolution"),
        "nonverbal_label_code": infer_nonverbal_label(path),
        "annotation_segment_count": len(annotations),
        "frame_count_mean": safe_mean(frame_counts),
        "frame_count_max": max(frame_counts) if frame_counts else None,
        "frame_count_min": min(frame_counts) if frame_counts else None,
        "keypoint_count_mean": safe_mean(keypoint_counts),
    }


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return

    fieldnames = list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def build_manifests(repo_root: Path, output_dir: Path) -> dict[str, Any]:
    linguistic_roots = [
        repo_root / "public_speaking_training_labels",
        repo_root / "public_speaking_validation_labels",
    ]

    linguistic_files: list[Path] = []
    nonverbal_files: list[Path] = []

    for root in linguistic_roots:
        if not root.exists():
            continue
        for path in root.rglob("*.json"):
            if path.name.endswith("_presentation.json"):
                linguistic_files.append(path)
            else:
                nonverbal_files.append(path)

    linguistic_rows = [parse_linguistic_record(path) for path in sorted(linguistic_files)]
    nonverbal_rows = [parse_nonverbal_record(path) for path in sorted(nonverbal_files)]

    write_csv(output_dir / "linguistic_manifest.csv", linguistic_rows)
    write_csv(output_dir / "nonverbal_manifest.csv", nonverbal_rows)

    summary = {
        "repo_root": str(repo_root),
        "linguistic_records": len(linguistic_rows),
        "nonverbal_records": len(nonverbal_rows),
        "linguistic_train_records": sum(1 for row in linguistic_rows if row["split"] == "train"),
        "linguistic_validation_records": sum(1 for row in linguistic_rows if row["split"] == "validation"),
        "nonverbal_train_records": sum(1 for row in nonverbal_rows if row["split"] == "train"),
        "nonverbal_validation_records": sum(1 for row in nonverbal_rows if row["split"] == "validation"),
        "linguistic_grade_distribution": dict(
            Counter(row["expert_grade_mode"] for row in linguistic_rows if row["expert_grade_mode"])
        ),
        "nonverbal_label_distribution": dict(
            Counter(row["nonverbal_label_code"] for row in nonverbal_rows if row["nonverbal_label_code"])
        ),
    }

    (output_dir / "dataset_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return summary


def main() -> None:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    output_dir = args.output_dir.resolve() if args.output_dir else (repo_root / "data" / "processed")

    summary = build_manifests(repo_root=repo_root, output_dir=output_dir)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
