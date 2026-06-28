from __future__ import annotations

import time

from application.graph.state import ContentState


def make_analytics_node():
    async def analytics_node(state: ContentState) -> dict:
        start = time.monotonic()
        review_output = state.review_output or {}
        draft_output = state.draft_output or {}

        review_score = review_output.get("score", 0)
        draft_body = draft_output.get("draft", {}).get("body", "")
        word_count = len(draft_body.split())

        if review_score >= 0.8:
            quality_label = "excellent"
        elif review_score >= 0.6:
            quality_label = "good"
        elif review_score >= 0.4:
            quality_label = "fair"
        else:
            quality_label = "needs_improvement"

        insights = [
            f"Post is {word_count} words",
            f"Quality score: {quality_label} ({review_score:.2f})",
        ]
        if word_count < 100:
            insights.append("Consider expanding for more depth")
        if review_score < 0.5:
            insights.append("Review flagged issues should be addressed before publishing")

        latency_ms = int((time.monotonic() - start) * 1000)
        result = {
            "quality_label": quality_label,
            "insights": insights,
            "recommendations": _generate_recommendations(state, quality_label),
            "latency_ms": latency_ms,
        }

        total_ms = sum(v for v in {**state.step_timing, "analytics": latency_ms}.values())
        final_output: dict = {
            "topic": state.topic,
            "quality_label": quality_label,
            "total_duration_ms": total_ms,
            "steps_completed": 9,
            "errors": list(state.errors),
        }

        return {
            "analytics_output": result,
            "final_output": final_output,
            "current_step": "analytics",
            "errors": list(state.errors),
            "step_timing": {**state.step_timing, "analytics": latency_ms},
        }

    return analytics_node


def _generate_recommendations(state: ContentState, quality_label: str) -> list[str]:
    recs: list[str] = []
    review = state.review_output or {}
    issues = review.get("issues", [])

    if quality_label == "needs_improvement":
        recs.append("Revise based on review feedback before publishing")
    if issues:
        recs.append(f"Address {len(issues)} issue(s) identified in review")
    recs.append("Schedule for optimal posting time")
    return recs
