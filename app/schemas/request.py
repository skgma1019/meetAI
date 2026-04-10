from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


ContextMode = Literal["presentation", "interview"]


class LanguageAnalyzeRequest(BaseModel):
    transcript: str = Field(..., min_length=1)
    context_mode: ContextMode = "presentation"
    expected_duration_sec: int | None = Field(default=None, ge=1)
    question_type: str | None = None
    role: str | None = None
    keywords: list[str] = Field(default_factory=list)


class NonverbalAnalyzeRequest(BaseModel):
    context_mode: ContextMode = "presentation"
    clip_duration_sec: float = Field(..., gt=0)
    hand_movement_events: int = Field(default=0, ge=0)
    head_movement_events: int = Field(default=0, ge=0)
    posture_shift_events: int = Field(default=0, ge=0)
    meaningless_gesture_events: int = Field(default=0, ge=0)


class FullAnalyzeRequest(BaseModel):
    context_mode: ContextMode = "presentation"
    language: LanguageAnalyzeRequest
    nonverbal: NonverbalAnalyzeRequest
