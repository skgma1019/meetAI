from __future__ import annotations

_GRADE_MAP: dict[int, str] = {
    5: "매우 좋음",
    4: "좋음",
    3: "보통",
    2: "개선 필요",
    1: "많은 연습 필요",
}

# Whisper avg_logprob 정규화 기준점
# -0.1 이상 → 100점 (매우 명확한 발음)
# -1.5 이하 → 0점  (불명확한 발음)
_LOGPROB_MAX = -0.1
_LOGPROB_MIN = -1.5


def score_pronunciation_from_logprob(avg_logprob: float | None) -> dict:
    """
    Whisper STT 신뢰도(avg_logprob)를 발음 점수로 변환.
    avg_logprob이 높을수록(0에 가까울수록) 발음이 명확함.

    반환:
      pronunciation_score      : 1~5 등급
      pronunciation_score_100  : 0~100 환산값
      pronunciation_grade      : 등급 문자열
    """
    if avg_logprob is None:
        return {
            "pronunciation_score": None,
            "pronunciation_score_100": None,
            "pronunciation_grade": None,
        }

    # 선형 정규화: [_LOGPROB_MIN, _LOGPROB_MAX] → [0, 100]
    score_100 = (avg_logprob - _LOGPROB_MIN) / (_LOGPROB_MAX - _LOGPROB_MIN) * 100
    score_100 = round(max(0.0, min(100.0, score_100)), 1)

    if score_100 >= 80:
        score = 5
    elif score_100 >= 60:
        score = 4
    elif score_100 >= 40:
        score = 3
    elif score_100 >= 20:
        score = 2
    else:
        score = 1

    return {
        "pronunciation_score": score,
        "pronunciation_score_100": score_100,
        "pronunciation_grade": _GRADE_MAP[score],
    }
