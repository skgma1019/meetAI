from __future__ import annotations


def build_feedback(context_mode: str, language_result: dict, nonverbal_result: dict, final_score: float) -> dict:
    deductions: list[str] = []
    recommendations: list[str] = []

    deductions.extend(language_result.get("detected_issues", [])[:2])
    deductions.extend(nonverbal_result.get("detected_issues", [])[:2])
    deductions = deductions[:3]

    if any("간투어" in issue for issue in language_result.get("detected_issues", [])):
        recommendations.append("문장을 시작하기 전에 1초 정도 쉬고 말해 간투어를 줄여보세요.")
    if any("반복" in issue for issue in language_result.get("detected_issues", [])):
        recommendations.append("핵심 문장을 먼저 정리해 같은 표현 반복을 줄여보세요.")
    if any("손동작" in issue for issue in nonverbal_result.get("detected_issues", [])):
        recommendations.append("손의 기본 위치를 정하고 필요한 순간에만 제스처를 사용해보세요.")
    if any("자세" in issue for issue in nonverbal_result.get("detected_issues", [])):
        recommendations.append("상체 중심을 먼저 고정한 뒤 문장 전환 때만 움직여보세요.")

    if not recommendations:
        recommendations.append("현재 강점을 유지하면서 답변 구조만 조금 더 선명하게 정리해보세요.")

    mode_label = "면접" if context_mode == "interview" else "발표"
    summary = (
        f"{mode_label} 코칭 결과 총점은 {final_score:.1f}점입니다. "
        f"언어 점수는 {language_result['overall_score']:.1f}점, "
        f"비언어 점수는 {nonverbal_result['overall_score']:.1f}점입니다."
    )

    return {
        "deductions": deductions,
        "recommendations": recommendations[:3],
        "summary": summary,
    }
