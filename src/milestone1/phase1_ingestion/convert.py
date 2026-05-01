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
    """Map one Hub row dict to ``Restaurant``, or ``None`` if the row should be skipped.

    Memory-conscious: optional descriptive fields the rest of the pipeline never reads
    (``address``, ``menu_sample``, ``dishes_liked``, ``url``, ``phone``,
    ``restaurant_type``, ``listing_type``, ``online_order``, ``book_table``,
    ``approx_cost_two_raw``) are intentionally **not** retained on the Restaurant.
    Each Hub row in this dataset can carry tens of KB of menu/review text; dropping it
    here keeps an 8 000-row in-memory load comfortably inside Render's free 512 MB tier.
    """
    name = _text(row.get(C.COL_NAME))
    if not name:
        return None

    city = _text(row.get(C.COL_LISTED_CITY)) or ""
    neighborhood = _text(row.get(C.COL_NEIGHBORHOOD)) or ""

    cuisines = parse_cuisines(row.get(C.COL_CUISINES))
    rating = parse_rating(row.get(C.COL_RATE))
    cost, _cost_raw = parse_approx_cost_two(row.get(C.COL_COST))
    band = budget_band_from_cost(cost)
    votes = parse_votes(row.get(C.COL_VOTES))

    rid = stable_restaurant_id(dedupe_key(name, city, neighborhood))

    return Restaurant(
        id=rid,
        name=name.strip(),
        city=city.strip(),
        neighborhood=neighborhood.strip(),
        address="",
        cuisines=cuisines,
        rating=rating,
        approx_cost_two=cost,
        approx_cost_two_raw=None,
        budget_band=band,
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


def _text(value: Any) -> str | None:
    if value is None:
        return None
    s = str(value).strip()
    return s if s else None
