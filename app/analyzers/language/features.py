from __future__ import annotations

import re


FILLER_PATTERNS = [
    r"음",
    r"어",
    r"저기",
    r"약간",
    r"그",
    r"뭔가",
    r"사실은",
]

INTRO_MARKERS = ["안녕하세요", "오늘", "먼저", "결론부터"]
BODY_MARKERS = ["첫째", "둘째", "예를 들어", "이유는", "구체적으로"]
OUTRO_MARKERS = ["정리하면", "결론적으로", "마지막으로", "이상입니다"]


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[가-힣A-Za-z0-9]+", text)


def _split_sentences(text: str) -> list[str]:
    return [segment.strip() for segment in re.split(r"[.!?\n]+", text) if segment.strip()]


def _count_fillers(text: str) -> int:
    return sum(len(re.findall(pattern, text)) for pattern in FILLER_PATTERNS)


def _repetition_ratio(tokens: list[str]) -> float:
    if len(tokens) < 2:
        return 0.0
    repeated_pairs = sum(1 for idx in range(1, len(tokens)) if tokens[idx] == tokens[idx - 1])
    return round(repeated_pairs / len(tokens), 6)


def _keyword_coverage(tokens: list[str], keywords: list[str]) -> float | None:
    if not keywords:
        return None
    token_set = set(tokens)
    matched = sum(1 for keyword in keywords if keyword in token_set)
    return round(matched / len(keywords), 6)


def _marker_score(text: str, markers: list[str]) -> float:
    if not markers:
        return 0.0
    matched = sum(1 for marker in markers if marker in text)
    return matched / len(markers)


def extract_language_features(transcript: str, keywords: list[str], expected_duration_sec: int | None) -> dict[str, float | int | None]:
    tokens = _tokenize(transcript)
    sentences = _split_sentences(transcript)
    avg_sentence_length = round(len(tokens) / len(sentences), 4) if sentences else 0.0

    expected_words = None
    if expected_duration_sec:
        expected_words = round(expected_duration_sec / 60 * 140)

    intro_score = _marker_score(transcript, INTRO_MARKERS)
    body_score = _marker_score(transcript, BODY_MARKERS)
    outro_score = _marker_score(transcript, OUTRO_MARKERS)

    return {
        "token_count": len(tokens),
        "sentence_count": len(sentences),
        "avg_sentence_length": avg_sentence_length,
        "filler_count": _count_fillers(transcript),
        "repetition_ratio": _repetition_ratio(tokens),
        "keyword_coverage": _keyword_coverage(tokens, keywords),
        "intro_marker_score": round(intro_score, 6),
        "body_marker_score": round(body_score, 6),
        "outro_marker_score": round(outro_score, 6),
        "expected_word_count": expected_words,
    }
