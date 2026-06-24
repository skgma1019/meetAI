from __future__ import annotations

from fastapi import APIRouter


router = APIRouter(prefix="/report", tags=["report"])


@router.get("/{report_id}", summary="리포트 조회", description="저장된 분석 리포트를 조회합니다. (미구현)")
def get_report(report_id: str) -> dict[str, str]:
    return {
        "report_id": report_id,
        "status": "not_implemented",
    }
