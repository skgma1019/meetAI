from __future__ import annotations

from fastapi import FastAPI

from app.api.routes_analysis import router as analysis_router
from app.api.routes_health import router as health_router
from app.api.routes_report import router as report_router
from app.api.routes_upload import router as upload_router
from app.core.config import settings


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description="Multimodal public speaking and interview coaching API.",
    )
    app.include_router(health_router)
    app.include_router(analysis_router)
    app.include_router(report_router)
    app.include_router(upload_router)
    return app


app = create_app()
