from __future__ import annotations

from pathlib import Path

from app.analyzers.language.baseline import LanguageBaselineModel, build_feature_row
from app.analyzers.language.features import extract_language_features
from app.analyzers.language.rubric import score_language_features
from app.schemas.request import LanguageAnalyzeRequest


_BASELINE_MODEL_PATH = Path("outputs/checkpoints/language_baseline.json")
_baseline_model: LanguageBaselineModel | None = None


def _get_baseline_model() -> LanguageBaselineModel | None:
    global _baseline_model
    if _baseline_model is not None:
        return _baseline_model
    if not _BASELINE_MODEL_PATH.exists():
        return None
    _baseline_model = LanguageBaselineModel.load(_BASELINE_MODEL_PATH)
    return _baseline_model


def _format_role(role: str | None) -> str:
    if not role:
        return "해당 직무"
    normalized = role.replace("_", " ").strip().lower()
    role_map = {
        "product manager": "프로덕트 매니저",
        "pm": "프로덕트 매니저",
        "data analyst": "데이터 분석가",
        "data scientist": "데이터 사이언티스트",
        "backend developer": "백엔드 개발자",
        "backend engineer": "백엔드 개발자",
        "frontend developer": "프론트엔드 개발자",
        "frontend engineer": "프론트엔드 개발자",
        "software engineer": "소프트웨어 엔지니어",
        "developer": "개발자",
        "designer": "디자이너",
        "marketer": "마케터",
    }
    return role_map.get(normalized, normalized)


def _format_keywords(keywords: list[str]) -> str:
    cleaned = [keyword.strip() for keyword in keywords if keyword.strip()]
    if not cleaned:
        return "문제 해결과 실행"
    if len(cleaned) == 1:
        return cleaned[0]
    if len(cleaned) == 2:
        return f"{cleaned[0]}와 {cleaned[1]}"
    return f"{cleaned[0]}, {cleaned[1]}, {cleaned[2]}"


def _build_strength_phrase(keywords: list[str]) -> str:
    cleaned = [keyword.strip() for keyword in keywords if keyword.strip()]
    if not cleaned:
        return "사용자 문제를 빠르게 파악하고 실행 가능한 해결책으로 연결하는"

    text = " ".join(cleaned)
    has_user = any(keyword in text for keyword in ["사용자", "고객", "유저"])
    has_analysis = any(keyword in text for keyword in ["분석", "데이터", "지표"])
    has_solution = any(keyword in text for keyword in ["개선", "해결", "원인", "전환율", "성과"])

    if has_user and has_analysis and has_solution:
        return "사용자 문제를 빠르게 파악하고 데이터 분석을 바탕으로 실행 가능한 해결책으로 연결하는"
    if has_user and has_analysis:
        return "사용자 문제를 파악하고 데이터 분석을 바탕으로 해결책을 만드는"
    if has_analysis and has_solution:
        return "데이터 분석을 통해 원인을 정리하고 개선안으로 연결하는"
    if len(cleaned) == 1:
        return f"{cleaned[0]}을 중심으로 문제를 정리하고 실행으로 연결하는"
    if len(cleaned) == 2:
        return f"{cleaned[0]}와 {cleaned[1]}을 바탕으로 해결책을 만드는"
    return "문제를 빠르게 파악하고 실행 가능한 해결책으로 연결하는"


def _build_readable_feedback(
    *,
    overall_score: float,
    rubric_result: dict,
    features: dict,
    context_mode: str,
) -> dict:
    strengths: list[str] = []
    weaknesses: list[str] = []
    next_actions: list[str] = []

    metric_map = {item["name"]: item["score"] for item in rubric_result["metrics"]}

    if metric_map.get("clarity", 0) >= 75:
        strengths.append("문장이 비교적 또렷하고 이해하기 쉽습니다.")
    if metric_map.get("fluency", 0) >= 75:
        strengths.append("간투어와 반복이 과도하지 않은 편입니다.")
    if metric_map.get("structure", 0) >= 70:
        strengths.append("도입-본론-결론 흐름이 어느 정도 보입니다.")
    if not strengths:
        strengths.append("기본 전달은 가능하며 문장을 끝까지 이어가는 힘은 있습니다.")

    if metric_map.get("structure", 0) < 60:
        weaknesses.append("답변 구조가 선명하지 않아 핵심이 늦게 드러납니다.")
        next_actions.append("첫 문장에 결론을 먼저 말하고, 그 뒤에 근거 두 가지만 붙여보세요.")
    if metric_map.get("question_fit", 0) < 50:
        weaknesses.append("질문 핵심 키워드 반영이 부족합니다.")
        next_actions.append("질문에서 나온 핵심 단어를 답변 안에 두세 번 자연스럽게 넣어보세요.")
    if features.get("filler_count", 0) >= 3:
        weaknesses.append("간투어가 들려 답변 신뢰감이 조금 떨어집니다.")
        next_actions.append("문장을 시작하기 전에 1초 쉬고 말해 간투어를 줄여보세요.")
    if metric_map.get("brevity", 0) < 55:
        weaknesses.append("답변 길이나 밀도가 상황에 비해 덜 맞습니다.")
        next_actions.append("답변을 60초에서 90초 길이로 압축해 말하는 연습을 해보세요.")

    label = "면접 답변" if context_mode == "interview" else "발표 답변"
    if overall_score >= 80:
        tone = "전반적으로 안정적입니다."
    elif overall_score >= 60:
        tone = "기본기는 괜찮지만 몇 군데만 다듬으면 더 좋아집니다."
    else:
        tone = "핵심 구조와 질문 적합성을 먼저 보완하는 게 좋습니다."

    return {
        "summary": f"{label} 기준 총점은 {overall_score:.1f}점입니다. {tone}",
        "strengths": strengths[:2],
        "weaknesses": weaknesses[:2],
        "next_actions": next_actions[:3] if next_actions else ["답변을 녹음해 듣고 첫 문장과 마지막 문장을 먼저 다듬어보세요."],
    }


def _build_improved_answer(payload: LanguageAnalyzeRequest, features: dict) -> str:
    role_text = _format_role(payload.role)
    keyword_phrase = _format_keywords(payload.keywords)
    strength_phrase = _build_strength_phrase(payload.keywords)
    sentence_count = int(features.get("sentence_count") or 0)

    if payload.context_mode == "interview" and payload.question_type == "self_intro":
        return (
            f"안녕하세요. 저는 {role_text} 직무에 지원한 지원자입니다. "
            f"결론부터 말씀드리면, 저는 {strength_phrase} 사람입니다. "
            f"이전 경험에서는 먼저 문제 상황을 빠르게 파악하고, 그다음 데이터를 바탕으로 원인을 정리한 뒤, 실행 가능한 개선안으로 연결했습니다. "
            f"예를 들어 핵심 병목을 찾아 개선했을 때 실제 성과 지표가 좋아진 경험이 있습니다. "
            f"입사 후에도 같은 방식으로 팀과 사용자에게 도움이 되는 결과를 만들겠습니다."
        )

    if sentence_count <= 4:
        detail_line = "답변이 너무 짧게 끝나지 않도록 근거 한 가지와 결과 한 가지를 꼭 붙여주세요."
    else:
        detail_line = "핵심 근거는 두 가지만 남기고 순서를 더 선명하게 정리해보세요."

    opener = "결론부터 말씀드리면" if payload.context_mode == "interview" else "오늘 말씀드릴 핵심은"
    closing = "이상입니다." if payload.context_mode == "presentation" else "이런 방식으로 기여하겠습니다."

    return (
        f"{opener}, 제 답변의 핵심은 {keyword_phrase}입니다. "
        f"먼저 상황이나 문제를 한 문장으로 명확히 설명하고, 다음으로 제가 취한 행동 두 가지를 순서대로 말씀드리겠습니다. "
        f"그 결과 어떤 변화나 성과가 있었는지 사례나 수치로 마무리하겠습니다. "
        f"{detail_line} "
        f"{closing}"
    )


def analyze_language(payload: LanguageAnalyzeRequest) -> dict:
    features = extract_language_features(
        transcript=payload.transcript,
        keywords=payload.keywords,
        expected_duration_sec=payload.expected_duration_sec,
    )
    rubric_result = score_language_features(features, payload.context_mode)

    baseline_feature_row = build_feature_row(
        {
            "split": "inference",
            "file_id": None,
            "speaker_age_flag": "unknown",
            "presentation_type": "unknown",
            "presentation_difficulty": "unknown",
            "audience_flag": "unknown",
            "word_count": features.get("token_count"),
            "audible_word_count": features.get("token_count"),
            "sentence_count": features.get("sentence_count"),
            "syllable_count": features.get("token_count", 0) * 3,
            "presentation_script_chars": len(payload.transcript),
            "stt_script_chars": len(payload.transcript),
            "fil_tag_count": features.get("filler_count"),
            "rep_tag_count": round((features.get("repetition_ratio") or 0.0) * (features.get("token_count") or 0)),
            "wr_tag_count": 0,
            "repeat_count_mean": round((features.get("repetition_ratio") or 0.0) * (features.get("token_count") or 0)),
            "filler_count_mean": features.get("filler_count"),
            "pause_count_mean": 0,
            "wrong_count_mean": 0,
            "voice_speed_mean": None,
            "voice_quality_score_mean": None,
            "expert_grade_score_mean": None,
        }
    )

    baseline_model = _get_baseline_model()
    baseline_grade_score = baseline_model.predict_score(baseline_feature_row) if baseline_model else None
    baseline_100 = round((baseline_grade_score / 10.0) * 100.0, 2) if baseline_grade_score is not None else None
    overall_score = rubric_result["overall_score"]
    readable_feedback = _build_readable_feedback(
        overall_score=overall_score,
        rubric_result=rubric_result,
        features=features,
        context_mode=payload.context_mode,
    )

    return {
        "overall_score": overall_score,
        "metrics": rubric_result["metrics"],
        "detected_issues": rubric_result["detected_issues"],
        "extracted_features": features,
        "model_outputs": {
            "rubric_score": rubric_result["overall_score"],
            "baseline_grade_score_10": baseline_grade_score,
            "baseline_score_100": baseline_100,
            "baseline_used_in_overall": 0,
        },
        "readable_feedback": readable_feedback,
        "improved_answer": _build_improved_answer(payload, features),
    }
