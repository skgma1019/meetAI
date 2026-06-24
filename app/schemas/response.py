from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ScoreItem(BaseModel):
    name: str = Field(..., description="지표 식별자 (예: clarity, fluency)")
    score: float = Field(..., ge=0, le=100, description="0~100점 점수")
    note: str | None = Field(default=None, description="지표 한국어 명칭")


class ReadableFeedback(BaseModel):
    summary: str = Field(..., description="전체 요약 문장")
    strengths: list[str] = Field(..., description="잘한 점 목록")
    weaknesses: list[str] = Field(..., description="개선이 필요한 점 목록")
    next_actions: list[str] = Field(..., description="구체적인 개선 행동 제안")


class LanguageAnalysisResponse(BaseModel):
    overall_score: float = Field(..., ge=0, le=100, description="언어 표현 종합 점수 (0~100)")
    metrics: list[ScoreItem] = Field(..., description="세부 지표별 점수 목록")
    detected_issues: list[str] = Field(..., description="감지된 언어 문제 목록")
    extracted_features: dict[str, float | int | None] = Field(..., description="전사문에서 추출된 원시 피처값")
    model_outputs: dict[str, float | int | None] = Field(
        default_factory=dict,
        description="ML 모델 추론 결과 (rubric_score, baseline_grade_score_10 등)",
    )
    readable_feedback: ReadableFeedback = Field(..., description="사람이 읽을 수 있는 피드백")
    improved_answer: str | None = Field(default=None, description="AI가 제안하는 개선 답변 예시")


class NonverbalAnalysisResponse(BaseModel):
    overall_score: float = Field(..., ge=0, le=100, description="비언어 표현 종합 점수 (0~100)")
    metrics: list[ScoreItem] = Field(..., description="자세·손동작·머리동작·신뢰감 세부 점수")
    detected_issues: list[str] = Field(..., description="감지된 비언어 문제 목록")
    extracted_features: dict[str, float | int | None] = Field(..., description="분당 이벤트 발생률 등 비언어 피처값")
    readable_feedback: ReadableFeedback = Field(..., description="사람이 읽을 수 있는 피드백")
    model_outputs: dict | None = Field(default=None, description="모델 분류 결과 (키포인트 분석 시에만 포함)")


class GeminiFeedback(BaseModel):
    overall_comment: str = Field(..., description="전체 총평")
    strengths: list[str] = Field(..., description="잘한 점")
    improvements: list[str] = Field(..., description="개선할 점")
    nonverbal_feedback: str = Field(..., description="비언어 표현 피드백")
    language_feedback: str = Field(..., description="언어 표현 피드백")


class AudioAnalysisResponse(BaseModel):
    transcript: str = Field(..., description="Whisper STT 전사문")
    audio_duration_sec: float | None = Field(default=None, description="오디오 길이(초)")
    language: LanguageAnalysisResponse = Field(..., description="언어 분석 결과")
    history_id: str | None = Field(default=None, description="저장된 분석 기록 ID (로그인 시)")
    posture_score: float | None = Field(default=None, description="자세 안정성 점수 (영상 업로드 시)")
    gaze_score: float | None = Field(default=None, description="시선 안정성 점수 (영상 업로드 시)")
    gesture_score: float | None = Field(default=None, description="손동작 적절성 점수 (영상 업로드 시)")
    nonverbal_score: float | None = Field(default=None, description="비언어 종합 점수 (영상 업로드 시)")
    gemini_feedback: GeminiFeedback | None = Field(default=None, description="Gemini AI 종합 피드백")
    pronunciation_score: int | None = Field(default=None, description="발음 점수 1~5")
    pronunciation_score_100: float | None = Field(default=None, description="발음 점수 0~100 환산")
    pronunciation_grade: str | None = Field(default=None, description="발음 등급 (매우 좋음 ~ 많은 연습 필요)")


class FullAnalysisResponse(BaseModel):
    context_mode: Literal["presentation", "interview"] = Field(..., description="분석 모드")
    history_id: str | None = Field(default=None, description="저장된 분석 기록 ID (로그인 시)")
    language: LanguageAnalysisResponse = Field(..., description="언어 분석 결과")
    nonverbal: NonverbalAnalysisResponse = Field(..., description="비언어 분석 결과")
    final_score: float = Field(..., ge=0, le=100, description="언어·비언어 가중 합산 최종 점수")
    weights: dict[str, float] = Field(..., description="언어·비언어 가중치 (context_mode에 따라 달라짐)")
    deductions: list[str] = Field(..., description="감점 요인 목록")
    recommendations: list[str] = Field(..., description="우선 개선 권고 사항")
    summary: str = Field(..., description="최종 코칭 요약 문장")
    readable_feedback: ReadableFeedback = Field(..., description="통합 피드백 (강점·약점·다음 행동)")
