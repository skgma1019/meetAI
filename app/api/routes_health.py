from __future__ import annotations

from fastapi import APIRouter


router = APIRouter(tags=["health"])


@router.get("/health", summary="서버 상태 확인", description="서버가 정상 동작 중인지 확인합니다.")
def health() -> dict[str, str]:
    return {"status": "ok"}
