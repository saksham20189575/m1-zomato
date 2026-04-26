import pytest

from milestone1.phase1_ingestion.model import BudgetBand
from milestone1.phase2_preferences.parse import (
    parse_budget_band,
    parse_cuisine_list,
    parse_minimum_rating,
)


def test_parse_budget_band_empty_and_enum() -> None:
    assert parse_budget_band(None) is None
    assert parse_budget_band("") is None
    assert parse_budget_band("  ") is None
    assert parse_budget_band("LOW") == BudgetBand.LOW
    assert parse_budget_band(BudgetBand.MEDIUM) == BudgetBand.MEDIUM
    assert parse_budget_band("unknown") is None
    assert parse_budget_band("nope") is None


def test_parse_minimum_rating() -> None:
    assert parse_minimum_rating(None) is None
    assert parse_minimum_rating("") is None
    assert parse_minimum_rating(3.5) == 3.5
    assert parse_minimum_rating("4") == 4.0
    with pytest.raises(ValueError):
        parse_minimum_rating("x")
    with pytest.raises(ValueError):
        parse_minimum_rating(True)


def test_parse_cuisine_list() -> None:
    assert parse_cuisine_list("A, B | C") == ("A", "B", "C")
    assert parse_cuisine_list([" x ", "y"]) == ("x", "y")
