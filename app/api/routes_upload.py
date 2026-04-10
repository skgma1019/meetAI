from __future__ import annotations

from fastapi import APIRouter


router = APIRouter(prefix="/upload", tags=["upload"])


@router.post("/video")
def upload_video() -> dict[str, str]:
    return {"status": "not_implemented"}
