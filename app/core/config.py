from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "meetAI")
    app_env: str = os.getenv("APP_ENV", "development")
    app_host: str = os.getenv("APP_HOST", "0.0.0.0")
    app_port: int = int(os.getenv("APP_PORT", "8000"))

    # 언어 + 비언어 + 발음 가중치 (합계 = 1.0)
    presentation_language_weight: float    = float(os.getenv("PRESENTATION_LANGUAGE_WEIGHT",    "0.60"))
    presentation_nonverbal_weight: float   = float(os.getenv("PRESENTATION_NONVERBAL_WEIGHT",   "0.25"))
    presentation_pronunciation_weight: float = float(os.getenv("PRESENTATION_PRONUNCIATION_WEIGHT", "0.15"))

    interview_language_weight: float       = float(os.getenv("INTERVIEW_LANGUAGE_WEIGHT",       "0.60"))
    interview_nonverbal_weight: float      = float(os.getenv("INTERVIEW_NONVERBAL_WEIGHT",      "0.25"))
    interview_pronunciation_weight: float  = float(os.getenv("INTERVIEW_PRONUNCIATION_WEIGHT",  "0.15"))


settings = Settings()
