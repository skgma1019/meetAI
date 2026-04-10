from __future__ import annotations

from app.core.config import settings


def fuse_scores(context_mode: str, language_score: float, nonverbal_score: float) -> dict:
    if context_mode == "interview":
        language_weight = settings.interview_language_weight
        nonverbal_weight = settings.interview_nonverbal_weight
    else:
        language_weight = settings.presentation_language_weight
        nonverbal_weight = settings.presentation_nonverbal_weight

    final_score = round(language_score * language_weight + nonverbal_score * nonverbal_weight, 2)
    return {
        "final_score": final_score,
        "weights": {
            "language": language_weight,
            "nonverbal": nonverbal_weight,
        },
    }
