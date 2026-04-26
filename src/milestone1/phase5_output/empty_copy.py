from __future__ import annotations

from enum import StrEnum

from milestone1.phase4_llm.model import RecommendResult


class EmptyPresentationKind(StrEnum):
    """Which empty or informational shell to show."""

    RESULTS = "results"
    NO_FILTER_MATCH = "no_filter_match"
    LLM_NO_PICKS = "llm_no_picks"


def presentation_kind(result: RecommendResult) -> EmptyPresentationKind:
    if result.source == "no_candidates" or result.candidate_count == 0:
        return EmptyPresentationKind.NO_FILTER_MATCH
    if not result.rankings and result.candidate_count > 0:
        return EmptyPresentationKind.LLM_NO_PICKS
    return EmptyPresentationKind.RESULTS


def empty_state_headline(kind: EmptyPresentationKind) -> str | None:
    if kind is EmptyPresentationKind.NO_FILTER_MATCH:
        return "No restaurants match filters"
    if kind is EmptyPresentationKind.LLM_NO_PICKS:
        return "LLM could not justify picks"
    return None


def empty_state_body(kind: EmptyPresentationKind) -> str | None:
    if kind is EmptyPresentationKind.NO_FILTER_MATCH:
        return (
            "Nothing in the loaded dataset passed your hard filters (location, rating, "
            "budget band, cuisine). Try relaxing one constraint or loading more rows."
        )
    if kind is EmptyPresentationKind.LLM_NO_PICKS:
        return (
            "Restaurants matched your filters and were sent to the model, but it did not "
            "return any grounded picks from the candidate list."
        )
    return None
