from __future__ import annotations

# .env를 가장 먼저 로드 (os.getenv 사용 모듈보다 앞에)
from dotenv import load_dotenv
load_dotenv()

from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes_analysis import router as analysis_router
from app.api.routes_auth import router as auth_router
from app.api.routes_health import router as health_router
from app.api.routes_history import router as history_router
from app.api.routes_report import router as report_router
from app.api.routes_upload import router as upload_router
from app.core.config import settings


async def _preload_models() -> None:
    import asyncio
    print("[meetAI] Whisper 모델 사전 로딩 중…", flush=True)
    try:
        from app.services.stt_service import _get_model
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, _get_model)
        print("[meetAI] Whisper 모델 로딩 완료", flush=True)
    except Exception as e:
        print(f"[meetAI] Whisper 모델 로딩 실패 (첫 요청 시 로딩됨): {e}", flush=True)


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description=(
            "## meetAI 발표·면접 코칭 API\n\n"
            "한국어 공적 말하기 데이터셋을 기반으로 언어·비언어 표현을 분석하고 맞춤형 코칭 피드백을 제공합니다."
        ),
    )

    @app.on_event("startup")
    async def startup():
        await _preload_models()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 이메일 인증 후 Supabase가 리다이렉트하는 루트 — 프론트엔드로 해시를 그대로 전달
    @app.get("/", response_class=HTMLResponse, include_in_schema=False)
    async def root_redirect():
        return HTMLResponse("""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>meetAI</title></head>
<body>
<script>
  var dest = "http://localhost:5173/ui/" + window.location.hash;
  window.location.replace(dest);
</script>
<p>잠시만 기다려주세요…</p>
</body></html>""")

    app.include_router(health_router)
    app.include_router(auth_router)
    app.include_router(history_router)
    app.include_router(analysis_router)
    app.include_router(report_router)
    app.include_router(upload_router)

    dist_path = Path(__file__).resolve().parent / "ui" / "dist"
    if not dist_path.exists():
        dist_path.mkdir(parents=True, exist_ok=True)
    app.mount("/ui", StaticFiles(directory=str(dist_path), html=True), name="ui")

    return app


app = create_app()
