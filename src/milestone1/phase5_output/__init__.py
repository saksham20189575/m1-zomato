"""
Phase 5 — presentation: render recommendations, empty states, light telemetry.
"""

from milestone1.phase5_output.empty_copy import (
    EmptyPresentationKind,
    empty_state_body,
    empty_state_headline,
    presentation_kind,
)
from milestone1.phase5_output.observability import (
    emit_recommendation_telemetry,
    recommendation_telemetry_doc,
)
from milestone1.phase5_output.render import (
    render_ranking_markdown,
    render_ranking_plain,
    render_report_markdown,
    render_report_plain,
)

__all__ = [
    "EmptyPresentationKind",
    "emit_recommendation_telemetry",
    "empty_state_body",
    "empty_state_headline",
    "presentation_kind",
    "recommendation_telemetry_doc",
    "render_ranking_markdown",
    "render_ranking_plain",
    "render_report_markdown",
    "render_report_plain",
]
