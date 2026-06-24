from __future__ import annotations

from fastapi import Header, HTTPException
from app.core.supabase_client import get_supabase


async def get_current_user(authorization: str | None = Header(None)):
    """Authorization: Bearer <token> 헤더로 현재 유저를 반환. 인증 실패 시 401."""
    client = get_supabase()
    if not client:
        raise HTTPException(status_code=503, detail="인증 서비스를 사용할 수 없습니다.")
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="인증이 필요합니다.")
    token = authorization.split(" ", 1)[1]
    try:
        resp = client.auth.get_user(token)
        if not resp.user:
            raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다.")
        return resp.user
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="토큰 검증 실패")


async def get_optional_user(authorization: str | None = Header(None)):
    """인증 선택적. 토큰이 없거나 유효하지 않으면 None 반환."""
    client = get_supabase()
    if not client or not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization.split(" ", 1)[1]
    try:
        resp = client.auth.get_user(token)
        return resp.user if resp.user else None
    except Exception:
        return None
