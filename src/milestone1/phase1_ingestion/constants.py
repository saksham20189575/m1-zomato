"""Phase 1 — Hub dataset identity, schema contract, and budget thresholds."""

from __future__ import annotations

from milestone1.phase0.scope import DATASET_ID, DATASET_SPLIT

# Pinned revision (see docs/dataset-contract.md) for reproducible schema and bytes.
DATASET_REVISION = "5738e9eda2fad49ad51c6e0ed26e761d9b947133"

SPLIT = DATASET_SPLIT
DATASET_NAME = DATASET_ID

COL_ADDRESS = "address"
COL_COST = "approx_cost(for two people)"
COL_BOOK_TABLE = "book_table"
COL_CUISINES = "cuisines"
COL_DISH_LIKED = "dish_liked"
COL_LISTED_CITY = "listed_in(city)"
COL_LISTED_TYPE = "listed_in(type)"
COL_NEIGHBORHOOD = "location"
COL_MENU = "menu_item"
COL_NAME = "name"
COL_ONLINE_ORDER = "online_order"
COL_PHONE = "phone"
COL_RATE = "rate"
COL_REST_TYPE = "rest_type"
COL_REVIEWS = "reviews_list"
COL_URL = "url"
COL_VOTES = "votes"

REQUIRED_HF_COLUMNS: frozenset[str] = frozenset(
    {
        COL_ADDRESS,
        COL_COST,
        COL_BOOK_TABLE,
        COL_CUISINES,
        COL_DISH_LIKED,
        COL_LISTED_CITY,
        COL_LISTED_TYPE,
        COL_NEIGHBORHOOD,
        COL_MENU,
        COL_NAME,
        COL_ONLINE_ORDER,
        COL_PHONE,
        COL_RATE,
        COL_REST_TYPE,
        COL_REVIEWS,
        COL_URL,
        COL_VOTES,
    }
)

BUDGET_LOW_MAX_INR = 500
BUDGET_MEDIUM_MAX_INR = 1200
