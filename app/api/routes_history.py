from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.auth import get_current_user
from app.core.supabase_client import get_supabase

router = APIRouter(prefix="/history", tags=["history"])


class VideoPathBody(BaseModel):
    video_path: str


def _client():
    c = get_supabase()
    if not c:
        raise HTTPException(status_code=503, detail="Supabase가 설정되지 않았습니다.")
    return c


@router.get("", summary="내 분석 기록 목록")
async def list_history(user=Depends(get_current_user)):
    client = _client()
    try:
        result = (
            client.table("analysis_history")
            .select("id,mode,overall_score,improved_answer,video_path,created_at")
            .eq("user_id", str(user.id))
            .order("created_at", desc=True)
            .limit(50)
            .execute()
        )
        return result.data or []
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{history_id}", summary="분석 기록 상세")
async def get_history(history_id: str, user=Depends(get_current_user)):
    client = _client()
    try:
        result = (
            client.table("analysis_history")
            .select("*")
            .eq("id", history_id)
            .eq("user_id", str(user.id))
            .single()
            .execute()
        )
        if not result.data:
            raise HTTPException(status_code=404, detail="기록을 찾을 수 없습니다.")
        return result.data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{history_id}/video", summary="영상 경로 업데이트")
async def update_video_path(history_id: str, body: VideoPathBody, user=Depends(get_current_user)):
    client = _client()
    try:
        result = (
            client.table("analysis_history")
            .update({"video_path": body.video_path})
            .eq("id", history_id)
            .eq("user_id", str(user.id))
            .execute()
        )
        return {"ok": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{history_id}", summary="기록 삭제")
async def delete_history(history_id: str, user=Depends(get_current_user)):
    client = _client()
    try:
        client.table("analysis_history").delete().eq("id", history_id).eq("user_id", str(user.id)).execute()
        return {"ok": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
