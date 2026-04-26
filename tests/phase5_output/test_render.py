from __future__ import annotations

from milestone1.phase1_ingestion.model import BudgetBand, Restaurant
from milestone1.phase4_llm.model import RankedRecommendation, RecommendResult
from milestone1.phase5_output.render import render_ranking_markdown, render_report_markdown


def _r() -> Restaurant:
    return Restaurant(
        id="id1",
        name="Cafe X",
        city="Mumbai",
        neighborhood="",
        address="",
        cuisines=("Italian", "Cafe"),
        rating=4.2,
        approx_cost_two=800,
        approx_cost_two_raw="800",
        budget_band=BudgetBand.MEDIUM,
        votes=2,
        restaurant_type=None,
        listing_type=None,
        online_order=None,
        book_table=None,
        menu_sample=None,
        dishes_liked=None,
        url=None,
        phone=None,
    )


def test_render_ranking_includes_required_fields() -> None:
    md = render_ranking_markdown(
        RankedRecommendation(
            restaurant_id="id1",
            rank=1,
            explanation="Great pasta.",
            restaurant=_r(),
        )
    )
    assert "Cafe X" in md
    assert "Italian" in md and "Cafe" in md
    assert "4.2" in md
    assert "₹800" in md
    assert "Great pasta." in md


def test_render_report_empty_filter() -> None:
    res = RecommendResult(
        source="no_candidates",
        rankings=(),
        matched_count=0,
        candidate_count=0,
        usage=None,
        latency_ms=None,
        detail=None,
    )
    out = render_report_markdown(res)
    assert "No restaurants match filters" in out


def test_render_report_llm_no_picks_copy() -> None:
    res = RecommendResult(
        source="llm",
        rankings=(),
        matched_count=5,
        candidate_count=4,
        usage=None,
        latency_ms=1.0,
        detail=None,
    )
    out = render_report_markdown(res)
    assert "LLM could not justify picks" in out
