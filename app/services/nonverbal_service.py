from __future__ import annotations

from app.schemas.request import NonverbalAnalyzeRequest


def _rate_per_minute(event_count: int, duration_sec: float) -> float:
    if duration_sec <= 0:
        return 0.0
    return round(event_count / (duration_sec / 60.0), 4)


def _bounded_score(base_score: float, penalty: float) -> float:
    return max(0.0, min(100.0, round(base_score - penalty, 2)))


def analyze_nonverbal(payload: NonverbalAnalyzeRequest) -> dict:
    hand_rate = _rate_per_minute(payload.hand_movement_events, payload.clip_duration_sec)
    head_rate = _rate_per_minute(payload.head_movement_events, payload.clip_duration_sec)
    posture_rate = _rate_per_minute(payload.posture_shift_events, payload.clip_duration_sec)
    meaningless_rate = _rate_per_minute(payload.meaningless_gesture_events, payload.clip_duration_sec)

    posture_score = _bounded_score(100.0, posture_rate * 8.0)
    hand_score = _bounded_score(100.0, hand_rate * 7.0)
    head_score = _bounded_score(100.0, head_rate * 6.0)
    trust_score = _bounded_score(100.0, (hand_rate + head_rate + posture_rate + meaningless_rate) * 4.0)

    overall_score = round(
        posture_score * 0.30 + hand_score * 0.25 + head_score * 0.20 + trust_score * 0.25,
        2,
    )

    detected_issues: list[str] = []
    if hand_rate > 3:
        detected_issues.append("불필요한 손동작 빈도가 높습니다.")
    if posture_rate > 2:
        detected_issues.append("자세 흔들림이 잦습니다.")
    if head_rate > 2:
        detected_issues.append("머리 움직임이 불안정합니다.")
    if meaningless_rate > 2:
        detected_issues.append("의미 없는 반동성 제스처가 감지되었습니다.")

    strengths: list[str] = []
    weaknesses: list[str] = []
    next_actions: list[str] = []

    if posture_score >= 85:
        strengths.append("자세 안정성이 비교적 좋습니다.")
    if hand_score >= 85:
        strengths.append("손동작이 과하게 흔들리지는 않습니다.")
    if not strengths:
        strengths.append("기본적인 비언어 표현은 유지하고 있습니다.")

    if hand_rate > 3:
        weaknesses.append("불필요한 손동작이 다소 많습니다.")
        next_actions.append("손의 기본 위치를 정해두고 문장 전환 때만 제스처를 사용해보세요.")
    if posture_rate > 2:
        weaknesses.append("상체 중심이 흔들리는 편입니다.")
        next_actions.append("발 간격을 고정하고 상체 중심을 먼저 잡은 뒤 말해보세요.")
    if head_rate > 2:
        weaknesses.append("머리 움직임이 잦아 시선 안정감이 떨어질 수 있습니다.")
        next_actions.append("한 문장마다 시선을 한 번만 이동하는 식으로 제한해보세요.")
    if not next_actions:
        next_actions.append("좋은 자세를 유지한 채 손동작만 목적 있게 쓰는 연습을 이어가세요.")

    readable_feedback = {
        "summary": f"비언어 표현 점수는 {overall_score:.1f}점입니다. 전체적으로 안정적인 편입니다." if overall_score >= 80 else f"비언어 표현 점수는 {overall_score:.1f}점입니다. 자세와 움직임을 조금 더 정리하면 좋아집니다.",
        "strengths": strengths[:2],
        "weaknesses": weaknesses[:2],
        "next_actions": next_actions[:3],
    }

    return {
        "overall_score": overall_score,
        "metrics": [
            {"name": "posture_stability", "score": posture_score, "note": "자세 안정성"},
            {"name": "hand_control", "score": hand_score, "note": "손동작 억제"},
            {"name": "head_stability", "score": head_score, "note": "머리동작 안정성"},
            {"name": "trust_presence", "score": trust_score, "note": "전체 신뢰감"},
        ],
        "detected_issues": detected_issues,
        "extracted_features": {
            "clip_duration_sec": payload.clip_duration_sec,
            "hand_event_rate_per_min": hand_rate,
            "head_event_rate_per_min": head_rate,
            "posture_event_rate_per_min": posture_rate,
            "meaningless_event_rate_per_min": meaningless_rate,
        },
        "readable_feedback": readable_feedback,
    }
