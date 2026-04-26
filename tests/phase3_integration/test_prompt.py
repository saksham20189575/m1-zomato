from __future__ import annotations

from milestone1.phase1_ingestion.model import BudgetBand, Restaurant
from milestone1.phase2_preferences.model import UserPreferences
from milestone1.phase3_integration.prompt import build_prompt_payload


def _one_restaurant() -> Restaurant:
    return Restaurant(
        id="abc123",
        name="Test|Kitchen",
        city="Mumbai",
        neighborhood="Colaba",
        address="1 Main",
        cuisines=("Chinese", "Thai"),
        rating=4.2,
        approx_cost_two=900,
        approx_cost_two_raw="900",
        budget_band=BudgetBand.MEDIUM,
        votes=12,
        restaurant_type=None,
        listing_type=None,
        online_order=None,
        book_table=None,
        menu_sample=None,
        dishes_liked=None,
        url=None,
        phone=None,
    )


def test_prompt_contains_preferences_candidates_and_grounding() -> None:
    prefs = UserPreferences(
        location="Mumbai",
        budget_band=BudgetBand.LOW,
        cuisines=("Chinese",),
        minimum_rating=3.5,
        additional_preferences="quiet dinner",
    )
    r = _one_restaurant()
    p = build_prompt_payload(prefs, (r,))

    assert "ONLY recommend" in p.system_message
    assert "rankings" in p.system_message
    assert "abc123" in p.user_message
    assert "Test\\|Kitchen" in p.user_message
    assert "Mumbai" in p.user_message
    assert "quiet dinner" in p.user_message
    assert '"location": "Mumbai"' in p.user_message
    assert "| id | name |" in p.user_message
