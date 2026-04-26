import pytest

from milestone1.phase1_ingestion import constants as C
from milestone1.phase1_ingestion.convert import row_to_restaurant
from milestone1.phase1_ingestion.errors import IngestionError
from milestone1.phase1_ingestion.load import assert_hub_row_schema
from milestone1.phase1_ingestion.model import BudgetBand


def _full_row(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        C.COL_ADDRESS: "12 MG Road",
        C.COL_COST: "600",
        C.COL_BOOK_TABLE: "Yes",
        C.COL_CUISINES: "Cafe, Italian",
        C.COL_DISH_LIKED: "Pasta",
        C.COL_LISTED_CITY: "Bangalore",
        C.COL_LISTED_TYPE: "Delivery",
        C.COL_NEIGHBORHOOD: "Indiranagar",
        C.COL_MENU: "Coffee",
        C.COL_NAME: "Test Cafe",
        C.COL_ONLINE_ORDER: "No",
        C.COL_PHONE: "123",
        C.COL_RATE: "4.1/5",
        C.COL_REST_TYPE: "Casual Dining",
        C.COL_REVIEWS: "[]",
        C.COL_URL: "https://example.com",
        C.COL_VOTES: "42",
    }
    base.update(overrides)
    return base


def test_assert_hub_row_schema_ok() -> None:
    assert_hub_row_schema(_full_row())


def test_assert_hub_row_schema_missing() -> None:
    row = _full_row()
    del row[C.COL_URL]
    with pytest.raises(IngestionError, match="missing required"):
        assert_hub_row_schema(row)


def test_row_to_restaurant_maps_fields() -> None:
    r = row_to_restaurant(_full_row())
    assert r is not None
    assert r.name == "Test Cafe"
    assert r.city == "Bangalore"
    assert r.neighborhood == "Indiranagar"
    assert r.cuisines == ("Cafe", "Italian")
    assert r.rating == 4.1
    assert r.approx_cost_two == 600
    assert r.budget_band == BudgetBand.MEDIUM
    assert r.votes == 42
    assert r.book_table is True
    assert r.online_order is False


def test_row_to_restaurant_skips_blank_name() -> None:
    assert row_to_restaurant(_full_row(**{C.COL_NAME: "  "})) is None
    assert row_to_restaurant(_full_row(**{C.COL_NAME: ""})) is None
