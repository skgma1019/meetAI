from __future__ import annotations

import re


FILLER_PATTERNS = [
    r"음+",
    r"어+",
    r"저기",
    r"약간",
    r"그+",
    r"뭔가",
    r"사실은",
]

# ── 도입부 마커 ────────────────────────────────────────────────────
# Primary: 명시적 인사 + 주제 제시 → A/B 등급 신호
INTRO_PRIMARY = [
    "안녕하세요",                                    # 명시적 인사
    "오늘 발표", "오늘 말씀", "발표하겠", "소개하겠",  # 주제 선언
    "결론부터 말씀", "먼저 말씀드리",                  # 선결론형 도입
]
# Secondary: 자기소개·주제 암시 → C/D 등급 신호
INTRO_SECONDARY = [
    "저는", "제가", "저희는",          # 자기소개
    "지원한", "지원했", "지원하게",    # 지원 관련 (면접)
    "오늘", "먼저", "안녕",           # 간접 도입
    "말씀드리겠", "소개해",            # 발표 선언
]

# ── 본론 마커 ─────────────────────────────────────────────────────
# Primary: 명시적 구성 신호 → A/B 등급 (논리 전개·예시·전환)
BODY_PRIMARY = [
    "첫째", "둘째", "셋째",                          # 나열 구조
    "첫 번째", "두 번째", "세 번째",
    "예를 들어", "이유는", "왜냐하면",                # 논거
    "구체적으로", "실제로", "사실",                   # 구체화
    "이에 따라", "그 결과", "따라서",                 # 인과 전환
]
# Secondary: 경험·내용 서술 → C/D 등급 (구체적 내용은 있으나 구성 신호 약함)
BODY_SECONDARY = [
    "특히", "또한", "그리고", "뿐만 아니라", "더불어",  # 연결어
    "경험", "개발", "진행", "담당", "참여", "구현", "설계",
    "있으며", "있고", "했고", "했으며", "했습니다",
    "이전", "당시", "결과", "성과", "통해",
    "년간", "개월간", "기간",
]

# ── 결론 마커 ─────────────────────────────────────────────────────
# Primary: 명시적 결론 선언 → A/B 등급
OUTRO_PRIMARY = [
    "정리하면", "결론적으로", "마지막으로",   # 결론 선언
    "이상입니다", "이상으로",                # 발표 종료
    "지금까지", "여기서",                   # 마무리 신호
]
# Secondary: 마무리 의지·인사 → C/D 등급
OUTRO_SECONDARY = [
    "감사합니다", "부탁드립니다",            # 마무리 인사
    "싶습니다", "하겠습니다", "드리겠습니다", # 의지 표현
    "기여하고", "기여할", "기여하겠",
    "노력하겠", "자신 있습니다",
    "함께", "나아가겠", "기대합니다",
]


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[가-힣A-Za-z0-9]+", text)


def _split_sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"[.!?\n]+", text) if s.strip()]


def _count_fillers(text: str) -> int:
    return sum(len(re.findall(pattern, text)) for pattern in FILLER_PATTERNS)


def _repetition_ratio(tokens: list[str]) -> float:
    if len(tokens) < 2:
        return 0.0
    repeated_pairs = sum(1 for i in range(1, len(tokens)) if tokens[i] == tokens[i - 1])
    return round(repeated_pairs / len(tokens), 6)


def _keyword_coverage(tokens: list[str], keywords: list[str]) -> float | None:
    if not keywords:
        return None
    token_set = set(tokens)
    matched = sum(1 for kw in keywords if kw in token_set)
    return round(matched / len(keywords), 6)


def _section_score(text: str, primary: list[str], secondary: list[str]) -> float:
    """
    AI Hub 공적말하기 전문가 평가 기준 — 5등급 섹션 점수 (0.0~1.0).

    A등급 (1.00): primary ≥2 개  또는  primary ≥1 + secondary ≥2
    B등급 (0.80): primary ≥1  +  secondary ≥1
    C등급 (0.60): primary ≥1  (secondary 없음)
    D등급 (0.40): secondary ≥2  (primary 없음, 간접 신호만)
    F등급 (0.00): 마커 없음
    """
    if not text:
        return 0.0
    p = sum(1 for m in primary if m in text)
    s = sum(1 for m in secondary if m in text)

    if p >= 2 or (p >= 1 and s >= 2):
        return 1.00  # A
    if p >= 1 and s >= 1:
        return 0.80  # B
    if p >= 1:
        return 0.60  # C
    if s >= 2:
        return 0.40  # D
    return 0.00      # F


def _structure_scores(sentences: list[str]) -> tuple[float, float, float]:
    """
    문장 위치 기반 도입·본론·결론 점수 (AI Hub 5등급 척도, 0.0~1.0).

    - 도입: 첫 1~2문장
    - 본론: 중간 문장들
    - 결론: 마지막 1~2문장
    """
    n = len(sentences)
    if n == 0:
        return 0.0, 0.0, 0.0

    intro_text = " ".join(sentences[:min(2, n)])
    outro_text = " ".join(sentences[max(0, n - 2):])

    if n >= 4:
        body_text = " ".join(sentences[1:n - 1])
    elif n == 3:
        body_text = sentences[1]
    else:
        body_text = " ".join(sentences)

    intro_score = _section_score(intro_text, INTRO_PRIMARY, INTRO_SECONDARY)
    body_score = _section_score(body_text, BODY_PRIMARY, BODY_SECONDARY)
    outro_score = _section_score(outro_text, OUTRO_PRIMARY, OUTRO_SECONDARY)

    # 문장 2개 이하: 본론 전개 불가 → 본론 점수 50% 감산
    if n <= 2:
        body_score *= 0.5

    return intro_score, body_score, outro_score


def extract_language_features(
    transcript: str,
    keywords: list[str],
    expected_duration_sec: int | None,
) -> dict[str, float | int | None]:
    tokens = _tokenize(transcript)
    sentences = _split_sentences(transcript)
    avg_sentence_length = round(len(tokens) / len(sentences), 4) if sentences else 0.0

    expected_words = None
    if expected_duration_sec:
        expected_words = round(expected_duration_sec / 60 * 140)

    intro_score, body_score, outro_score = _structure_scores(sentences)

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
