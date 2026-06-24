from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, Field


ContextMode = Literal["presentation", "interview"]


class LanguageAnalyzeRequest(BaseModel):
    model_config = {"json_schema_extra": {"example": {
        "transcript": "안녕하세요. 저는 백엔드 개발자 직무에 지원했습니다. 저는 문제를 빠르게 파악하고 실행으로 연결하는 것을 잘합니다.",
        "context_mode": "interview",
        "expected_duration_sec": 90,
        "question_type": "self_intro",
        "role": "backend developer",
        "keywords": ["문제 해결", "실행력", "협업"],
    }}}

    transcript: str = Field(..., min_length=1, description="분석할 발화 전사문")
    context_mode: ContextMode = Field(
        default="presentation",
        description="`interview` (면접) 또는 `presentation` (발표) 중 선택",
    )
    expected_duration_sec: int | None = Field(
        default=None, ge=1,
        description="목표 발화 시간(초). 입력 시 속도·밀도 기준이 보정됩니다.",
    )
    question_type: str | None = Field(
        default=None,
        description="질문 유형. 예: `self_intro` (자기소개), `experience` (경험), `motivation` (지원 동기)",
    )
    role: str | None = Field(
        default=None,
        description="지원 직무. 예: `backend developer`, `product manager`, `data scientist`",
    )
    keywords: list[str] = Field(
        default_factory=list,
        description="답변에서 강조해야 할 핵심 키워드 목록",
    )


class NonverbalAnalyzeRequest(BaseModel):
    model_config = {"json_schema_extra": {"example": {
        "context_mode": "interview",
        "clip_duration_sec": 90.0,
        "hand_movement_events": 12,
        "head_movement_events": 8,
        "posture_shift_events": 3,
        "meaningless_gesture_events": 2,
    }}}

    context_mode: ContextMode = Field(
        default="presentation",
        description="`interview` (면접) 또는 `presentation` (발표) 중 선택",
    )
    clip_duration_sec: float = Field(..., gt=0, description="영상 클립 길이(초)")
    hand_movement_events: int = Field(default=0, ge=0, description="손동작 이벤트 횟수")
    head_movement_events: int = Field(default=0, ge=0, description="머리 움직임 이벤트 횟수")
    posture_shift_events: int = Field(default=0, ge=0, description="자세 흔들림 이벤트 횟수")
    meaningless_gesture_events: int = Field(default=0, ge=0, description="의미 없는 반동성 제스처 이벤트 횟수")


class FullAnalyzeRequest(BaseModel):
    model_config = {"json_schema_extra": {"example": {
        "context_mode": "interview",
        "language": {
            "transcript": "안녕하세요. 저는 백엔드 개발자 직무에 지원했습니다. 저는 문제를 빠르게 파악하고 실행으로 연결하는 것을 잘합니다.",
            "context_mode": "interview",
            "expected_duration_sec": 90,
            "role": "backend developer",
            "keywords": ["문제 해결", "실행력"],
        },
        "nonverbal": {
            "context_mode": "interview",
            "clip_duration_sec": 90.0,
            "hand_movement_events": 12,
            "head_movement_events": 8,
            "posture_shift_events": 3,
            "meaningless_gesture_events": 2,
        },
    }}}

    context_mode: ContextMode = Field(
        default="presentation",
        description="`interview` (면접) 또는 `presentation` (발표) 중 선택",
    )
    language: LanguageAnalyzeRequest = Field(..., description="언어 분석 입력값")
    nonverbal: NonverbalAnalyzeRequest = Field(..., description="비언어 분석 입력값")
    history_id: str | None = Field(default=None, description="기존 history 레코드 ID (업데이트용)")
    pronunciation_score_100: float | None = Field(
        default=None, ge=0, le=100,
        description="발음 점수 0~100 (upload/audio에서 반환된 값을 전달)",
    )


# Keypoint: [x, y, z] — 3개 좌표값
Keypoint = Annotated[list[float], Field(min_length=2, max_length=3)]
# Frame: 18개 키포인트
Frame = Annotated[list[Keypoint], Field(min_length=1, max_length=18)]


class NonverbalKeypointRequest(BaseModel):
    model_config = {"json_schema_extra": {"example": {
        "context_mode": "interview",
        "clip_duration_sec": 90.0,
        "clips": [
            {
                "frames": [
                    [[917, 231, 1562], [933, 219, 1588], [906, 221, 1590],
                     [968, 243, 1688], [888, 245, 1705], [930, 318, 1728],
                     [1012, 352, 1714], [858, 360, 1720], [1032, 484, 1740],
                     [833, 494, 1754], [1037, 591, 1685], [821, 604, 1717],
                     [978, 575, 1772], [896, 575, 1789], [982, 766, 1823],
                     [900, 761, 1859], [988, 928, 1947], [910, 932, 1952]],
                ]
            }
        ],
    }}}

    context_mode: ContextMode = Field(
        default="presentation",
        description="`interview` (면접) 또는 `presentation` (발표) 중 선택",
    )
    clip_duration_sec: float = Field(..., gt=0, description="영상 전체 길이(초)")
    clips: list[dict[str, list[Frame]]] = Field(
        ...,
        description=(
            "클립 목록. 각 클립은 `{\"frames\": [[keypoint, ...], ...]}` 형태. "
            "클립 1개 = 약 1~3초 구간. "
            "각 프레임은 18개 키포인트([x, y, z])로 구성됩니다."
        ),
    )
