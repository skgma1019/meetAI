from __future__ import annotations

from pydantic import BaseModel


class CoachingReport(BaseModel):
    summary: str
    deductions: list[str]
    recommendations: list[str]
