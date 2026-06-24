from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.auth import get_optional_user
from app.core.supabase_client import get_supabase
from app.schemas.request import FullAnalyzeRequest, LanguageAnalyzeRequest, NonverbalAnalyzeRequest, NonverbalKeypointRequest
from app.schemas.response import FullAnalysisResponse, LanguageAnalysisResponse, NonverbalAnalysisResponse
from app.services.feedback_service import build_feedback
from app.services.fusion_service import fuse_scores
from app.services.language_service import analyze_language
from app.services.nonverbal_service import analyze_nonverbal, analyze_nonverbal_keypoints


router = APIRouter(prefix="/analyze", tags=["analysis"])


def _upsert_full_history(
    history_id: str | None,
    user_id: str,
    mode: str,
    transcript: str,
    language_result: dict,
    nonverbal_result: dict,
    final_score: float,
    full_response_dict: dict,
) -> str | None:
    client = get_supabase()
    if not client:
        return None
    try:
        record = {
            "user_id": user_id,
            "mode": mode,
            "transcript": transcript,
            "overall_score": final_score,
            "rubric_score": (language_result.get("model_outputs") or {}).get("rubric_score"),
            "feedback": full_response_dict,
            "improved_answer": language_result.get("improved_answer"),
        }
        if history_id:
            result = (
                client.table("analysis_history")
                .update(record)
                .eq("id", history_id)
                .eq("user_id", user_id)
                .execute()
            )
            return history_id
        else:
            result = client.table("analysis_history").insert(record).execute()
            return result.data[0]["id"] if result.data else None
    except Exception as e:
        import traceback
        print(f"[meetAI] full history 저장 실패: {e}", flush=True)
        traceback.print_exc()
        return None


@router.post(
    "/language",
    response_model=LanguageAnalysisResponse,
    summary="언어 표현 분석",
)
def analyze_language_route(payload: LanguageAnalyzeRequest) -> LanguageAnalysisResponse:
    result = analyze_language(payload)
    return LanguageAnalysisResponse(**result)


@router.post(
    "/nonverbal/keypoints",
    response_model=NonverbalAnalysisResponse,
    summary="비언어 표현 분석 (키포인트)",
)
def analyze_nonverbal_keypoints_route(payload: NonverbalKeypointRequest) -> NonverbalAnalysisResponse:
    result = analyze_nonverbal_keypoints(payload)
    return NonverbalAnalysisResponse(**result)


@router.post(
    "/nonverbal",
    response_model=NonverbalAnalysisResponse,
    summary="비언어 표현 분석",
)
def analyze_nonverbal_route(payload: NonverbalAnalyzeRequest) -> NonverbalAnalysisResponse:
    result = analyze_nonverbal(payload)
    return NonverbalAnalysisResponse(**result)


@router.post(
    "/full",
    response_model=FullAnalysisResponse,
    summary="통합 분석 (언어 + 비언어)",
)
async def analyze_full_route(payload: FullAnalyzeRequest, user=Depends(get_optional_user)) -> FullAnalysisResponse:
    language_payload = payload.language.model_copy(update={"context_mode": payload.context_mode})
    nonverbal_payload = payload.nonverbal.model_copy(update={"context_mode": payload.context_mode})

    language_result = analyze_language(language_payload)
    nonverbal_result = analyze_nonverbal(nonverbal_payload)
    fusion_result = fuse_scores(
        context_mode=payload.context_mode,
        language_score=language_result["overall_score"],
        nonverbal_score=nonverbal_result["overall_score"],
        pronunciation_score_100=payload.pronunciation_score_100,
    )
    feedback = build_feedback(
        context_mode=payload.context_mode,
        language_result=language_result,
        nonverbal_result=nonverbal_result,
        final_score=fusion_result["final_score"],
    )

    response = FullAnalysisResponse(
        context_mode=payload.context_mode,
        language=LanguageAnalysisResponse(**language_result),
        nonverbal=NonverbalAnalysisResponse(**nonverbal_result),
        final_score=fusion_result["final_score"],
        weights=fusion_result["weights"],
        deductions=feedback["deductions"],
        recommendations=feedback["recommendations"],
        summary=feedback["summary"],
        readable_feedback={
            "summary": feedback["summary"],
            "strengths": [
                *language_result["readable_feedback"]["strengths"][:1],
                *nonverbal_result["readable_feedback"]["strengths"][:1],
            ][:2],
            "weaknesses": [
                *language_result["readable_feedback"]["weaknesses"][:1],
                *nonverbal_result["readable_feedback"]["weaknesses"][:1],
            ][:2],
            "next_actions": feedback["recommendations"][:3],
        },
    )

    if user:
        history_id = _upsert_full_history(
            history_id=payload.history_id,
            user_id=str(user.id),
            mode=payload.context_mode,
            transcript=payload.language.transcript,
            language_result=language_result,
            nonverbal_result=nonverbal_result,
            final_score=fusion_result["final_score"],
            full_response_dict=response.model_dump(mode="json"),
        )
        response = response.model_copy(update={"history_id": history_id})

    return response
