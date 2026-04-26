import pytest

from milestone1.phase1_ingestion.model import BudgetBand
from milestone1.phase1_ingestion.normalize import (
    budget_band_from_cost,
    parse_approx_cost_two,
    parse_cuisines,
    parse_rating,
    parse_votes,
    parse_yes_no,
    stable_restaurant_id,
)


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("4.1/5", 4.1),
        ("4.2", 4.2),
        (" 3.0 / 5 ", 3.0),
        ("-", None),
        ("NEW", None),
        ("", None),
        (None, None),
        ("not-a-number", None),
    ],
)
def test_parse_rating(raw: str | None, expected: float | None) -> None:
    assert parse_rating(raw) == expected


@pytest.mark.parametrize(
    "raw,parsed,raw_out",
    [
        ("800", 800, "800"),
        ("₹1,200", 1200, "₹1,200"),
        ("", None, None),
        (None, None, None),
        ("-", None, "-"),
    ],
)
def test_parse_approx_cost_two(raw: str | None, parsed: int | None, raw_out: str | None) -> None:
    p, r = parse_approx_cost_two(raw)
    assert p == parsed
    assert r == raw_out


@pytest.mark.parametrize(
    "cost,band",
    [
        (None, BudgetBand.UNKNOWN),
        (400, BudgetBand.LOW),
        (500, BudgetBand.LOW),
        (501, BudgetBand.MEDIUM),
        (1200, BudgetBand.MEDIUM),
        (1201, BudgetBand.HIGH),
    ],
)
def test_budget_band_from_cost(cost: int | None, band: BudgetBand) -> None:
    assert budget_band_from_cost(cost) == band


def test_parse_cuisines_splits() -> None:
    assert parse_cuisines("Chinese, Italian") == ("Chinese", "Italian")
    assert parse_cuisines("North Indian | Mughlai") == ("North Indian", "Mughlai")
    assert parse_cuisines("") == ()
    assert parse_cuisines(None) == ()


def test_parse_votes_and_yes_no() -> None:
    assert parse_votes("120") == 120
    assert parse_votes("x") is None
    assert parse_yes_no("Yes") is True
    assert parse_yes_no("no") is False
    assert parse_yes_no("maybe") is None


def test_stable_restaurant_id_deterministic() -> None:
    k = "jalsa|bangalore|indiranagar"
    assert stable_restaurant_id(k) == stable_restaurant_id(k)
    assert len(stable_restaurant_id(k)) == 16
