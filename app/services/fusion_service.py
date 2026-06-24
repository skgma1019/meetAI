from __future__ import annotations

from app.core.config import settings


def fuse_scores(
    context_mode: str,
    language_score: float,
    nonverbal_score: float,
    pronunciation_score_100: float | None = None,
) -> dict:
    """
    언어 + 비언어 + 발음(선택) 가중 합산.
    발음 점수가 None이면 언어·비언어 두 가지만 정규화해 계산.
    """
    if context_mode == "interview":
        lw = settings.interview_language_weight
        nw = settings.interview_nonverbal_weight
        pw = settings.interview_pronunciation_weight
    else:
        lw = settings.presentation_language_weight
        nw = settings.presentation_nonverbal_weight
        pw = settings.presentation_pronunciation_weight

    if pronunciation_score_100 is not None:
        # 3-way 가중 합산
        final_score = round(
            language_score * lw
            + nonverbal_score * nw
            + pronunciation_score_100 * pw,
            2,
        )
        weights = {"language": lw, "nonverbal": nw, "pronunciation": pw}
    else:
        # 발음 점수 없음 → 언어·비언어만 정규화
        total = lw + nw
        lw_n = lw / total
        nw_n = nw / total
        final_score = round(language_score * lw_n + nonverbal_score * nw_n, 2)
        weights = {"language": round(lw_n, 4), "nonverbal": round(nw_n, 4)}

    return {"final_score": final_score, "weights": weights}
