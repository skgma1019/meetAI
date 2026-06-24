from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile

from app.core.auth import get_optional_user
from app.core.supabase_client import get_supabase
from app.schemas.request import ContextMode, LanguageAnalyzeRequest
from app.schemas.response import AudioAnalysisResponse, LanguageAnalysisResponse
from app.services.language_service import analyze_language
from app.services.stt_service import transcribe_bytes

router = APIRouter(prefix="/upload", tags=["upload"])

_ALLOWED_SUFFIXES = {".mp3", ".mp4", ".wav", ".m4a", ".webm", ".ogg", ".flac"}


def _save_audio_history(user_id: str, mode: str, transcript: str, language_result: dict, audio_duration_sec: float | None) -> str | None:
    client = get_supabase()
    if not client:
        return None
    try:
        record = {
            "user_id": user_id,
            "mode": mode,
            "transcript": transcript,
            "overall_score": language_result.get("overall_score"),
            "rubric_score": (language_result.get("model_outputs") or {}).get("rubric_score"),
            "feedback": {
                "language": language_result,
                "audio_duration_sec": audio_duration_sec,
            },
            "improved_answer": language_result.get("improved_answer"),
        }
        result = client.table("analysis_history").insert(record).execute()
        return result.data[0]["id"] if result.data else None
    except Exception as e:
        import traceback
        print(f"[meetAI] history 저장 실패: {e}", flush=True)
        traceback.print_exc()
        return None


@router.post(
    "/audio",
    response_model=AudioAnalysisResponse,
    summary="오디오 업로드 → STT → 언어 분석",
)
async def upload_audio(
    file: UploadFile,
    context_mode: ContextMode = Query(default="presentation"),
    expected_duration_sec: int | None = Query(default=None, ge=1),
    role: str | None = Query(default=None),
    keywords: str = Query(default=""),
    user=Depends(get_optional_user),
) -> AudioAnalysisResponse:
    suffix = "." + (file.filename or "audio").rsplit(".", 1)[-1].lower()
    if suffix not in _ALLOWED_SUFFIXES:
        raise HTTPException(
            status_code=415,
            detail=f"지원하지 않는 파일 형식입니다. 허용 형식: {', '.join(sorted(_ALLOWED_SUFFIXES))}",
        )

    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="빈 파일입니다.")

    try:
        stt_result = transcribe_bytes(data, suffix=suffix)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"전사 중 오류가 발생했습니다: {exc}") from exc

    transcript: str = stt_result["text"]
    if not transcript:
        raise HTTPException(status_code=422, detail="전사 결과가 비어 있습니다. 음성이 포함된 파일인지 확인하세요.")

    keyword_list = [k.strip() for k in keywords.split(",") if k.strip()]
    analysis_payload = LanguageAnalyzeRequest(
        transcript=transcript,
        context_mode=context_mode,
        expected_duration_sec=expected_duration_sec,
        role=role,
        keywords=keyword_list,
    )
    language_result = analyze_language(analysis_payload)
    audio_duration_sec = stt_result.get("duration_sec")

    history_id: str | None = None
    if user:
        history_id = _save_audio_history(
            user_id=str(user.id),
            mode=context_mode,
            transcript=transcript,
            language_result=language_result,
            audio_duration_sec=audio_duration_sec,
        )

    return AudioAnalysisResponse(
        transcript=transcript,
        audio_duration_sec=audio_duration_sec,
        language=LanguageAnalysisResponse(**language_result),
        history_id=history_id,
    )


@router.post("/video", summary="영상 업로드 (오디오와 동일)", include_in_schema=True)
async def upload_video(
    file: UploadFile,
    context_mode: ContextMode = Query(default="presentation"),
    expected_duration_sec: int | None = Query(default=None, ge=1),
    role: str | None = Query(default=None),
    keywords: str = Query(default=""),
    user=Depends(get_optional_user),
) -> AudioAnalysisResponse:
    return await upload_audio(
        file=file,
        context_mode=context_mode,
        expected_duration_sec=expected_duration_sec,
        role=role,
        keywords=keywords,
        user=user,
    )
