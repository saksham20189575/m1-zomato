import pytest

from milestone1.phase1_ingestion.model import BudgetBand, Restaurant
from milestone1.phase2_preferences import (
    allowed_cities_from_restaurants,
    preferences_from_mapping,
)
from milestone1.phase2_preferences.constants import MAX_ADDITIONAL_PREFERENCE_CHARS
from milestone1.phase2_preferences.errors import PreferencesValidationError


def _restaurant(name: str, city: str) -> Restaurant:
    return Restaurant(
        id=name.lower(),
        name=name,
        city=city,
        neighborhood="",
        address="",
        cuisines=(),
        rating=4.0,
        approx_cost_two=500,
        approx_cost_two_raw="500",
        budget_band=BudgetBand.LOW,
        votes=None,
        restaurant_type=None,
        listing_type=None,
        online_order=None,
        book_table=None,
        menu_sample=None,
        dishes_liked=None,
        url=None,
        phone=None,
    )


def test_preferences_happy_path() -> None:
    p = preferences_from_mapping(
        {
            "location": " Bangalore ",
            "budget": "medium",
            "cuisine": "Italian, Chinese",
            "minimum_rating": "3.5",
            "notes": "  family friendly  ",
        }
    )
    assert p.location == "Bangalore"
    assert p.budget_band == BudgetBand.MEDIUM
    assert p.cuisines == ("Italian", "Chinese")
    assert p.minimum_rating == 3.5
    assert p.additional_preferences == "family friendly"


def test_preferences_any_budget_and_cuisine() -> None:
    p = preferences_from_mapping({"location": "Delhi"})
    assert p.budget_band is None
    assert p.cuisines == ()
    assert p.minimum_rating is None
    assert p.additional_preferences is None


def test_location_required() -> None:
    with pytest.raises(PreferencesValidationError) as ei:
        preferences_from_mapping({"location": ""})
    assert any(f == "location" for f, _ in ei.value.errors)


def test_rating_range() -> None:
    with pytest.raises(PreferencesValidationError) as ei:
        preferences_from_mapping({"location": "X", "minimum_rating": 6})
    assert ei.value.errors[0][0] == "minimum_rating"


def test_additional_too_long() -> None:
    with pytest.raises(PreferencesValidationError) as ei:
        preferences_from_mapping(
            {"location": "X", "additional": "a" * (MAX_ADDITIONAL_PREFERENCE_CHARS + 1)}
        )
    assert ei.value.errors[0][0] == "additional_preferences"


def test_allowed_cities_match_case_insensitive() -> None:
    p = preferences_from_mapping(
        {"location": "bangalore"},
        allowed_city_names=("Bangalore", "Delhi"),
    )
    assert p.location == "Bangalore"


def test_allowed_cities_unknown() -> None:
    with pytest.raises(PreferencesValidationError) as ei:
        preferences_from_mapping(
            {"location": "Paris"},
            allowed_city_names=("Bangalore",),
        )
    assert ei.value.errors[0][0] == "location"


def test_allowed_cities_from_restaurants() -> None:
    rows = (_restaurant("A", "Bangalore"), _restaurant("B", "Bangalore"), _restaurant("C", "Delhi"))
    cities = allowed_cities_from_restaurants(rows)
    assert cities == frozenset({"Bangalore", "Delhi"})
