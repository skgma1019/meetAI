from __future__ import annotations

from fastapi import APIRouter


router = APIRouter(prefix="/report", tags=["report"])


@router.get("/{report_id}")
def get_report(report_id: str) -> dict[str, str]:
    return {
        "report_id": report_id,
        "status": "not_implemented",
    }
