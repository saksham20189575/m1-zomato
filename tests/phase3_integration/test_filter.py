from __future__ import annotations

from milestone1.phase1_ingestion.model import BudgetBand, Restaurant
from milestone1.phase2_preferences.model import UserPreferences
from milestone1.phase3_integration.filter import filter_and_rank


def _r(
    *,
    rid: str,
    city: str = "Mumbai",
    cuisines: tuple[str, ...] = ("Chinese",),
    rating: float | None = 4.0,
    budget_band: BudgetBand = BudgetBand.MEDIUM,
    votes: int | None = 5,
) -> Restaurant:
    return Restaurant(
        id=rid,
        name=f"R-{rid}",
        city=city,
        neighborhood="X",
        address="",
        cuisines=cuisines,
        rating=rating,
        approx_cost_two=800,
        approx_cost_two_raw="800",
        budget_band=budget_band,
        votes=votes,
        restaurant_type=None,
        listing_type=None,
        online_order=None,
        book_table=None,
        menu_sample=None,
        dishes_liked=None,
        url=None,
        phone=None,
    )


def test_no_matches_wrong_city() -> None:
    prefs = UserPreferences(
        location="Mumbai",
        budget_band=None,
        cuisines=(),
        minimum_rating=None,
        additional_preferences=None,
    )
    rows = [_r(rid="a", city="Delhi")]
    capped, n = filter_and_rank(rows, prefs, cap=10)
    assert n == 0
    assert capped == ()


def test_cuisine_overlap_required() -> None:
    prefs = UserPreferences(
        location="Mumbai",
        budget_band=None,
        cuisines=("Italian",),
        minimum_rating=None,
        additional_preferences=None,
    )
    rows = [_r(rid="a", cuisines=("Chinese",))]
    capped, n = filter_and_rank(rows, prefs, cap=10)
    assert n == 0


def test_cuisine_case_insensitive() -> None:
    prefs = UserPreferences(
        location="Mumbai",
        budget_band=None,
        cuisines=("chinese",),
        minimum_rating=None,
        additional_preferences=None,
    )
    rows = [_r(rid="a", cuisines=("Chinese",))]
    capped, n = filter_and_rank(rows, prefs, cap=10)
    assert n == 1
    assert capped[0].id == "a"


def test_minimum_rating_excludes_unknown_rating() -> None:
    prefs = UserPreferences(
        location="Mumbai",
        budget_band=None,
        cuisines=(),
        minimum_rating=3.0,
        additional_preferences=None,
    )
    rows = [_r(rid="a", rating=None), _r(rid="b", rating=4.0)]
    capped, n = filter_and_rank(rows, prefs, cap=10)
    assert n == 1
    assert capped[0].id == "b"


def test_budget_max_band_medium_allows_low() -> None:
    prefs = UserPreferences(
        location="Mumbai",
        budget_band=BudgetBand.MEDIUM,
        cuisines=(),
        minimum_rating=None,
        additional_preferences=None,
    )
    rows = [_r(rid="low", budget_band=BudgetBand.LOW), _r(rid="high", budget_band=BudgetBand.HIGH)]
    capped, n = filter_and_rank(rows, prefs, cap=10)
    assert n == 1
    assert capped[0].id == "low"


def test_too_many_matches_respects_cap() -> None:
    prefs = UserPreferences(
        location="Mumbai",
        budget_band=None,
        cuisines=(),
        minimum_rating=None,
        additional_preferences=None,
    )
    rows = [_r(rid=f"id{i:03d}") for i in range(50)]
    capped, n = filter_and_rank(rows, prefs, cap=12)
    assert n == 50
    assert len(capped) == 12


def test_ranking_prefers_higher_rating_then_votes() -> None:
    prefs = UserPreferences(
        location="Mumbai",
        budget_band=None,
        cuisines=(),
        minimum_rating=None,
        additional_preferences=None,
    )
    rows = [
        _r(rid="a", rating=3.0, votes=100),
        _r(rid="b", rating=4.5, votes=1),
        _r(rid="c", rating=4.5, votes=50),
    ]
    capped, n = filter_and_rank(rows, prefs, cap=10)
    assert n == 3
    assert [r.id for r in capped] == ["c", "b", "a"]
