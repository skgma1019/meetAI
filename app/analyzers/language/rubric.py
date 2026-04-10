from __future__ import annotations


def _clip(score: float) -> float:
    return round(max(0.0, min(100.0, score)), 2)


def score_language_features(features: dict, context_mode: str) -> dict:
    token_count = float(features.get("token_count") or 0)
    avg_sentence_length = float(features.get("avg_sentence_length") or 0)
    filler_count = float(features.get("filler_count") or 0)
    repetition_ratio = float(features.get("repetition_ratio") or 0)
    keyword_coverage = features.get("keyword_coverage")
    intro_marker_score = float(features.get("intro_marker_score") or 0)
    body_marker_score = float(features.get("body_marker_score") or 0)
    outro_marker_score = float(features.get("outro_marker_score") or 0)

    structure_signal = (intro_marker_score + body_marker_score + outro_marker_score) / 3
    structure_score = _clip(structure_signal * 100)

    clarity_penalty = abs(avg_sentence_length - 16) * 2.2
    clarity_score = _clip(100 - clarity_penalty - repetition_ratio * 120)

    brevity_target = 180 if context_mode == "interview" else 260
    brevity_penalty = abs(token_count - brevity_target) / max(brevity_target, 1) * 80
    brevity_score = _clip(100 - brevity_penalty)

    fluency_penalty = filler_count * 4.5 + repetition_ratio * 160
    fluency_score = _clip(100 - fluency_penalty)

    if keyword_coverage is None:
        fit_score = 70.0
    else:
        fit_score = _clip(keyword_coverage * 100)

    overall_score = round(
        structure_score * 0.25
        + clarity_score * 0.20
        + brevity_score * 0.15
        + fluency_score * 0.20
        + fit_score * 0.20,
        2,
    )

    detected_issues: list[str] = []
    if filler_count >= 3:
        detected_issues.append("간투어가 자주 나타납니다.")
    if repetition_ratio >= 0.03:
        detected_issues.append("같은 표현의 반복 비율이 높습니다.")
    if structure_score < 55:
        detected_issues.append("도입-본론-결론 구조 신호가 약합니다.")
    if keyword_coverage is not None and keyword_coverage < 0.5:
        detected_issues.append("핵심 키워드 반영률이 낮습니다.")

    return {
        "overall_score": overall_score,
        "metrics": [
            {"name": "structure", "score": structure_score, "note": "도입-본론-결론 구조"},
            {"name": "clarity", "score": clarity_score, "note": "명확성"},
            {"name": "brevity", "score": brevity_score, "note": "간결성"},
            {"name": "fluency", "score": fluency_score, "note": "간투어와 반복 제어"},
            {"name": "question_fit", "score": fit_score, "note": "질문 적합성"},
        ],
        "detected_issues": detected_issues,
    }
