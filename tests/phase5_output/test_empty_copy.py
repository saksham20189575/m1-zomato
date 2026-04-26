from __future__ import annotations

from milestone1.phase1_ingestion.model import BudgetBand, Restaurant
from milestone1.phase4_llm.model import RankedRecommendation, RecommendResult
from milestone1.phase5_output.empty_copy import (
    EmptyPresentationKind,
    empty_state_headline,
    presentation_kind,
)


def _r() -> Restaurant:
    return Restaurant(
        id="x",
        name="N",
        city="C",
        neighborhood="",
        address="",
        cuisines=("A",),
        rating=4.0,
        approx_cost_two=500,
        approx_cost_two_raw="500",
        budget_band=BudgetBand.LOW,
        votes=1,
        restaurant_type=None,
        listing_type=None,
        online_order=None,
        book_table=None,
        menu_sample=None,
        dishes_liked=None,
        url=None,
        phone=None,
    )


def test_no_filter_match() -> None:
    res = RecommendResult(
        source="no_candidates",
        rankings=(),
        matched_count=0,
        candidate_count=0,
        usage=None,
        latency_ms=None,
        detail=None,
    )
    assert presentation_kind(res) is EmptyPresentationKind.NO_FILTER_MATCH
    assert empty_state_headline(EmptyPresentationKind.NO_FILTER_MATCH) == "No restaurants match filters"


def test_llm_no_picks() -> None:
    res = RecommendResult(
        source="llm",
        rankings=(),
        matched_count=10,
        candidate_count=5,
        usage=None,
        latency_ms=1.0,
        detail=None,
    )
    assert presentation_kind(res) is EmptyPresentationKind.LLM_NO_PICKS


def test_results_when_rankings_present() -> None:
    item = RankedRecommendation(
        restaurant_id="x",
        rank=1,
        explanation="ok",
        restaurant=_r(),
    )
    res = RecommendResult(
        source="llm",
        rankings=(item,),
        matched_count=3,
        candidate_count=3,
        usage=None,
        latency_ms=1.0,
        detail=None,
    )
    assert presentation_kind(res) is EmptyPresentationKind.RESULTS
