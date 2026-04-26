from __future__ import annotations

from milestone1.phase1_ingestion.model import BudgetBand, Restaurant
from milestone1.phase4_llm.fallback import deterministic_fallback_rankings


def _r(rid: str) -> Restaurant:
    return Restaurant(
        id=rid,
        name=f"N-{rid}",
        city="Mumbai",
        neighborhood="",
        address="",
        cuisines=("X",),
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


def test_fallback_respects_top_k() -> None:
    rows = [_r("1"), _r("2"), _r("3")]
    out = deterministic_fallback_rankings(rows, top_k=2)
    assert len(out) == 2
    assert out[0].rank == 1 and out[1].rank == 2
    assert out[0].restaurant is not None and out[0].restaurant.id == "1"
