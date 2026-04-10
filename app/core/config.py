from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "meetAI")
    app_env: str = os.getenv("APP_ENV", "development")
    app_host: str = os.getenv("APP_HOST", "0.0.0.0")
    app_port: int = int(os.getenv("APP_PORT", "8000"))
    presentation_language_weight: float = float(os.getenv("DEFAULT_PRESENTATION_LANGUAGE_WEIGHT", "0.6"))
    presentation_nonverbal_weight: float = float(os.getenv("DEFAULT_PRESENTATION_NONVERBAL_WEIGHT", "0.4"))
    interview_language_weight: float = float(os.getenv("DEFAULT_INTERVIEW_LANGUAGE_WEIGHT", "0.7"))
    interview_nonverbal_weight: float = float(os.getenv("DEFAULT_INTERVIEW_NONVERBAL_WEIGHT", "0.3"))


settings = Settings()
