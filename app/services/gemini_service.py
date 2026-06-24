from __future__ import annotations

import json
import os
import re
from functools import lru_cache
from typing import Any


@lru_cache(maxsize=1)
def _get_model() -> Any | None:
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        print("[meetAI] GEMINI_API_KEY 미설정 — Gemini 피드백 비활성화", flush=True)
        return None
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")
        print("[meetAI] Gemini 1.5 Flash 연결됨", flush=True)
        return model
    except Exception as exc:
        print(f"[meetAI] Gemini 초기화 실패: {exc}", flush=True)
        return None


def generate_feedback(
    pose_result: dict,
    language_result: dict,
    context_mode: str,
    pronunciation_result: dict | None = None,
) -> dict | None:
    """
    Gemini 1.5 Flash로 종합 피드백 생성.
    실패 시 None 반환 (호출자가 룰 기반 폴백 처리).
    """
    model = _get_model()
    if model is None:
        return None

    mode_label = "면접" if context_mode == "interview" else "발표"
    lf = language_result
    features = lf.get("extracted_features", {})
    readable = lf.get("readable_feedback", {})

    filler_count = features.get("filler_count", 0)
    repetition_ratio = features.get("repetition_ratio", 0)
    strengths_txt = ", ".join(readable.get("strengths", [])) or "해당 없음"
    improvements_txt = ", ".join(readable.get("weaknesses", [])) or "해당 없음"

    # 발음 섹션 (있을 때만 포함)
    pronunciation_section = ""
    if pronunciation_result and pronunciation_result.get("pronunciation_score_100") is not None:
        pronunciation_section = (
            f"\n[발음 분석]\n"
            f"- 발음 점수: {pronunciation_result['pronunciation_score_100']:.1f}점\n"
            f"- 발음 등급: {pronunciation_result.get('pronunciation_grade', '보통')}"
        )

    prompt = f"""아래 {mode_label} 분석 결과를 바탕으로 한국어로 피드백해줘.

[언어 분석]
- 종합 점수: {lf.get("overall_score", 0):.1f}점
- 간투어 횟수: {filler_count}회
- 반복 비율: {repetition_ratio}
- 강점: {strengths_txt}
- 개선점: {improvements_txt}

[비언어 분석]
- 자세 안정성: {pose_result.get("posture_score", 75):.1f}점
- 시선 안정성: {pose_result.get("gaze_score", 75):.1f}점
- 손동작 적절성: {pose_result.get("gesture_score", 75):.1f}점{pronunciation_section}

다음 JSON 형식으로만 응답해줘 (```json 블록이나 설명 없이 JSON만):
{{
  "overall_comment": "전체 총평 2~3문장",
  "strengths": ["잘한 점 1", "잘한 점 2"],
  "improvements": ["개선할 점 1", "개선할 점 2"],
  "nonverbal_feedback": "비언어 표현 구체적 피드백 1~2문장",
  "language_feedback": "언어 표현 구체적 피드백 1~2문장"
}}"""

    try:
        response = model.generate_content(prompt)
        raw = response.text.strip()

        # ```json ... ``` 또는 ``` ... ``` 블록 제거
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)

        # JSON 객체만 추출 (앞뒤 잡음 제거)
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            raw = match.group()

        parsed = json.loads(raw)
        # 필수 키 검증
        required = {"overall_comment", "strengths", "improvements", "nonverbal_feedback", "language_feedback"}
        if not required.issubset(parsed.keys()):
            raise ValueError(f"필수 키 누락: {required - parsed.keys()}")

        return parsed

    except Exception as exc:
        print(f"[meetAI] Gemini 피드백 파싱 실패: {exc}", flush=True)
        return None
