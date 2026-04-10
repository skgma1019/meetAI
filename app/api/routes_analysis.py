from __future__ import annotations

from fastapi import APIRouter

from app.schemas.request import FullAnalyzeRequest, LanguageAnalyzeRequest, NonverbalAnalyzeRequest
from app.schemas.response import FullAnalysisResponse, LanguageAnalysisResponse, NonverbalAnalysisResponse
from app.services.feedback_service import build_feedback
from app.services.fusion_service import fuse_scores
from app.services.language_service import analyze_language
from app.services.nonverbal_service import analyze_nonverbal


router = APIRouter(prefix="/analyze", tags=["analysis"])


@router.post("/language", response_model=LanguageAnalysisResponse)
def analyze_language_route(payload: LanguageAnalyzeRequest) -> LanguageAnalysisResponse:
    result = analyze_language(payload)
    return LanguageAnalysisResponse(**result)


@router.post("/nonverbal", response_model=NonverbalAnalysisResponse)
def analyze_nonverbal_route(payload: NonverbalAnalyzeRequest) -> NonverbalAnalysisResponse:
    result = analyze_nonverbal(payload)
    return NonverbalAnalysisResponse(**result)


@router.post("/full", response_model=FullAnalysisResponse)
def analyze_full_route(payload: FullAnalyzeRequest) -> FullAnalysisResponse:
    language_payload = payload.language.model_copy(update={"context_mode": payload.context_mode})
    nonverbal_payload = payload.nonverbal.model_copy(update={"context_mode": payload.context_mode})

    language_result = analyze_language(language_payload)
    nonverbal_result = analyze_nonverbal(nonverbal_payload)
    fusion_result = fuse_scores(
        context_mode=payload.context_mode,
        language_score=language_result["overall_score"],
        nonverbal_score=nonverbal_result["overall_score"],
    )
    feedback = build_feedback(
        context_mode=payload.context_mode,
        language_result=language_result,
        nonverbal_result=nonverbal_result,
        final_score=fusion_result["final_score"],
    )

    return FullAnalysisResponse(
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
