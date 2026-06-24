from __future__ import annotations

import os
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile

from app.core.auth import get_optional_user
from app.core.supabase_client import get_supabase
from app.schemas.request import ContextMode, LanguageAnalyzeRequest
from app.schemas.response import AudioAnalysisResponse, LanguageAnalysisResponse
from app.services.language_service import analyze_language
from app.services.stt_service import transcribe_bytes, transcribe, _TEMP_DIR

router = APIRouter(prefix="/upload", tags=["upload"])

_ALLOWED_SUFFIXES = {".mp3", ".mp4", ".wav", ".m4a", ".webm", ".ogg", ".flac"}
_VIDEO_SUFFIXES   = {".mp4", ".webm"}


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


def _run_pronunciation(avg_logprob: float | None) -> dict:
    """Whisper avg_logprob → 발음 점수 변환. 실패 시 None 필드 dict 반환."""
    try:
        from app.services.pronunciation_service import score_pronunciation_from_logprob
        result = score_pronunciation_from_logprob(avg_logprob)
        print(
            f"[meetAI] 발음 채점 완료: score={result.get('pronunciation_score')} "
            f"({result.get('pronunciation_grade')}, logprob={avg_logprob:.3f})" if avg_logprob is not None
            else "[meetAI] 발음 채점: avg_logprob 없음",
            flush=True,
        )
        return result
    except Exception as exc:
        print(f"[meetAI] 발음 채점 실패: {exc}", flush=True)
        return {"pronunciation_score": None, "pronunciation_score_100": None, "pronunciation_grade": None}


def _run_pose_and_gemini(
    video_path: str,
    language_result: dict,
    context_mode: str,
    pronunciation_result: dict | None = None,
) -> tuple[dict | None, dict | None, float | None, dict | None]:
    """포즈 분석 + 점수 융합 + Gemini 피드백. 각각 실패해도 None 반환."""
    pose_result = None
    gemini_feedback = None
    final_score = None
    weights = None

    try:
        from app.services.pose_service import analyze_video
        pose_result = analyze_video(video_path)
        print(f"[meetAI] 포즈 분석 완료: nonverbal_score={pose_result.get('nonverbal_score')}", flush=True)
    except Exception as exc:
        print(f"[meetAI] 포즈 분석 실패: {exc}", flush=True)

    if pose_result:
        nonverbal_score_val = pose_result.get("nonverbal_score")
        if nonverbal_score_val is not None:
            # 비언어 점수가 있을 때만 fusion 계산
            try:
                from app.services.fusion_service import fuse_scores
                fusion = fuse_scores(
                    context_mode=context_mode,
                    language_score=language_result.get("overall_score", 0),
                    nonverbal_score=nonverbal_score_val,
                    pronunciation_score_100=(pronunciation_result or {}).get("pronunciation_score_100"),
                )
                final_score = fusion.get("final_score")
                weights = fusion.get("weights")
                print(f"[meetAI] 점수 융합 완료: final_score={final_score}", flush=True)
            except Exception as exc:
                print(f"[meetAI] 점수 융합 실패: {exc}", flush=True)
        else:
            print("[meetAI] 포즈 분석 결과 없음 → fusion 생략", flush=True)

        try:
            from app.services.feedback_service import build_feedback_with_gemini
            gemini_feedback = build_feedback_with_gemini(
                context_mode=context_mode,
                language_result=language_result,
                pose_result=pose_result,
                final_score=final_score or language_result.get("overall_score", 0),
                pronunciation_result=pronunciation_result,
            )
            if gemini_feedback:
                print("[meetAI] Gemini 피드백 생성 완료", flush=True)
        except Exception as exc:
            print(f"[meetAI] Gemini 피드백 실패: {exc}", flush=True)

    return pose_result, gemini_feedback, final_score, weights


@router.post(
    "/audio",
    response_model=AudioAnalysisResponse,
    summary="오디오/영상 업로드 → STT → 언어·발음 분석 (영상은 포즈·Gemini 포함)",
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

    is_video = suffix in _VIDEO_SUFFIXES

    # 모든 파일을 temp로 관리 (STT + 발음 채점 + 포즈 분석 공유)
    tmp_path = _TEMP_DIR / f"upload_{os.getpid()}_{id(data)}{suffix}"
    try:
        tmp_path.write_bytes(data)
        tmp_str = str(tmp_path)

        # ── STT ─────────────────────────────────────────────────
        try:
            stt_result = transcribe(tmp_str)
        except RuntimeError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"전사 중 오류: {exc}") from exc

        transcript: str = stt_result["text"]
        if not transcript:
            raise HTTPException(status_code=422, detail="전사 결과가 비어 있습니다. 음성이 포함된 파일인지 확인하세요.")

        audio_duration_sec = stt_result.get("duration_sec")
        avg_logprob = stt_result.get("avg_logprob")

        # ── 언어 분석 ────────────────────────────────────────────
        keyword_list = [k.strip() for k in keywords.split(",") if k.strip()]
        language_result = analyze_language(LanguageAnalyzeRequest(
            transcript=transcript,
            context_mode=context_mode,
            expected_duration_sec=expected_duration_sec,
            role=role,
            keywords=keyword_list,
        ))

        # ── 발음 채점 (Whisper 신뢰도 재활용, 추가 모델 없음) ────
        pronunciation_result = _run_pronunciation(avg_logprob)

        # ── 포즈·Gemini (영상만) ─────────────────────────────────
        pose_result: dict | None = None
        gemini_feedback: dict | None = None
        final_score: float | None = None
        fusion_weights: dict | None = None
        if is_video:
            pose_result, gemini_feedback, final_score, fusion_weights = _run_pose_and_gemini(
                video_path=tmp_str,
                language_result=language_result,
                context_mode=context_mode,
                pronunciation_result=pronunciation_result,
            )

    finally:
        tmp_path.unlink(missing_ok=True)

    # ── 히스토리 저장 ─────────────────────────────────────────────
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
        posture_score=pose_result.get("posture_score") if pose_result else None,
        gaze_score=pose_result.get("gaze_score") if pose_result else None,
        gesture_score=pose_result.get("gesture_score") if pose_result else None,
        nonverbal_score=pose_result.get("nonverbal_score") if pose_result else None,
        gemini_feedback=gemini_feedback,
        pronunciation_score=pronunciation_result.get("pronunciation_score"),
        pronunciation_score_100=pronunciation_result.get("pronunciation_score_100"),
        pronunciation_grade=pronunciation_result.get("pronunciation_grade"),
        final_score=final_score,
        weights=fusion_weights,
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
