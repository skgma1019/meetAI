from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel, EmailStr

from app.core.auth import get_current_user
from app.core.supabase_client import get_supabase

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterBody(BaseModel):
    email: str
    password: str
    username: str = ""


class LoginBody(BaseModel):
    email: str
    password: str


def _require_client():
    client = get_supabase()
    if not client:
        raise HTTPException(status_code=503, detail="Supabase가 설정되지 않았습니다. .env를 확인하세요.")
    return client


@router.post("/register", summary="회원가입")
async def register(body: RegisterBody):
    client = _require_client()
    try:
        resp = client.auth.sign_up({
            "email": body.email,
            "password": body.password,
            "options": {"data": {"username": body.username}},
        })
        if resp.user is None:
            raise HTTPException(status_code=400, detail="회원가입에 실패했습니다. 이미 사용 중인 이메일일 수 있습니다.")
        return {"message": "회원가입 성공. 이메일 인증을 완료해주세요.", "user_id": str(resp.user.id)}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login", summary="로그인 → JWT 반환")
async def login(body: LoginBody):
    client = _require_client()
    try:
        resp = client.auth.sign_in_with_password({"email": body.email, "password": body.password})
        if resp.session is None:
            raise HTTPException(status_code=401, detail="이메일 또는 비밀번호가 올바르지 않습니다.")
        return {
            "access_token": resp.session.access_token,
            "refresh_token": resp.session.refresh_token,
            "user": {
                "id": str(resp.user.id),
                "email": resp.user.email,
                "username": (resp.user.user_metadata or {}).get("username", ""),
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.post("/logout", summary="로그아웃")
async def logout(user=Depends(get_current_user)):
    # 세션 무효화는 클라이언트에서 처리; 서버는 확인만
    return {"message": "로그아웃 성공"}


@router.get("/me", summary="현재 유저 정보")
async def me(user=Depends(get_current_user)):
    return {
        "id": str(user.id),
        "email": user.email,
        "username": (user.user_metadata or {}).get("username", ""),
        "created_at": str(user.created_at),
    }
