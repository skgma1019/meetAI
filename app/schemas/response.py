from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ScoreItem(BaseModel):
    name: str
    score: float = Field(..., ge=0, le=100)
    note: str | None = None


class ReadableFeedback(BaseModel):
    summary: str
    strengths: list[str]
    weaknesses: list[str]
    next_actions: list[str]


class LanguageAnalysisResponse(BaseModel):
    overall_score: float = Field(..., ge=0, le=100)
    metrics: list[ScoreItem]
    detected_issues: list[str]
    extracted_features: dict[str, float | int | None]
    model_outputs: dict[str, float | int | None] = Field(default_factory=dict)
    readable_feedback: ReadableFeedback
    improved_answer: str | None = None


class NonverbalAnalysisResponse(BaseModel):
    overall_score: float = Field(..., ge=0, le=100)
    metrics: list[ScoreItem]
    detected_issues: list[str]
    extracted_features: dict[str, float | int | None]
    readable_feedback: ReadableFeedback


class FullAnalysisResponse(BaseModel):
    context_mode: Literal["presentation", "interview"]
    language: LanguageAnalysisResponse
    nonverbal: NonverbalAnalysisResponse
    final_score: float = Field(..., ge=0, le=100)
    weights: dict[str, float]
    deductions: list[str]
    recommendations: list[str]
    summary: str
    readable_feedback: ReadableFeedback
