from __future__ import annotations

from typing import Any, Mapping

from milestone1.phase1_ingestion import constants as C
from milestone1.phase1_ingestion.model import Restaurant
from milestone1.phase1_ingestion.normalize import (
    budget_band_from_cost,
    parse_approx_cost_two,
    parse_cuisines,
    parse_rating,
    parse_votes,
    parse_yes_no,
    stable_restaurant_id,
)


def dedupe_key(name: str, city: str, neighborhood: str) -> str:
    return f"{name.strip().lower()}|{city.strip().lower()}|{neighborhood.strip().lower()}"


def row_to_restaurant(row: Mapping[str, Any]) -> Restaurant | None:
    """Map one Hub row dict to ``Restaurant``, or ``None`` if the row should be skipped."""
    name = _text(row.get(C.COL_NAME))
    if not name:
        return None

    city = _text(row.get(C.COL_LISTED_CITY)) or ""
    neighborhood = _text(row.get(C.COL_NEIGHBORHOOD)) or ""
    address = _text(row.get(C.COL_ADDRESS)) or ""

    cuisines = parse_cuisines(row.get(C.COL_CUISINES))
    rating = parse_rating(row.get(C.COL_RATE))
    cost, cost_raw = parse_approx_cost_two(row.get(C.COL_COST))
    band = budget_band_from_cost(cost)

    votes = parse_votes(row.get(C.COL_VOTES))
    rest_type = _text(row.get(C.COL_REST_TYPE))
    listing_type = _text(row.get(C.COL_LISTED_TYPE))
    online = parse_yes_no(row.get(C.COL_ONLINE_ORDER))
    book = parse_yes_no(row.get(C.COL_BOOK_TABLE))

    menu = _text(row.get(C.COL_MENU))
    dishes = _text(row.get(C.COL_DISH_LIKED))
    url = _text(row.get(C.COL_URL))
    phone = _text(row.get(C.COL_PHONE))

    rid = stable_restaurant_id(dedupe_key(name, city, neighborhood))

    return Restaurant(
        id=rid,
        name=name.strip(),
        city=city.strip(),
        neighborhood=neighborhood.strip(),
        address=address.strip(),
        cuisines=cuisines,
        rating=rating,
        approx_cost_two=cost,
        approx_cost_two_raw=cost_raw,
        budget_band=band,
        votes=votes,
        restaurant_type=rest_type,
        listing_type=listing_type,
        online_order=online,
        book_table=book,
        menu_sample=menu,
        dishes_liked=dishes,
        url=url,
        phone=phone,
    )


def _text(value: Any) -> str | None:
    if value is None:
        return None
    s = str(value).strip()
    return s if s else None
