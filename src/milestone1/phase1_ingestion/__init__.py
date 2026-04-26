"""
Phase 1 — data ingestion and canonical restaurant model.

Public API for downstream phases: load/iterate typed ``Restaurant`` rows from the Hub.
"""

from milestone1.phase1_ingestion.constants import DATASET_REVISION, REQUIRED_HF_COLUMNS
from milestone1.phase1_ingestion.errors import IngestionError
from milestone1.phase1_ingestion.load import (
    assert_hub_row_schema,
    iter_restaurants,
    load_restaurants,
)
from milestone1.phase1_ingestion.model import BudgetBand, Restaurant
from milestone1.phase1_ingestion.normalize import (
    budget_band_from_cost,
    parse_approx_cost_two,
    parse_cuisines,
    parse_rating,
    parse_votes,
    parse_yes_no,
)

__all__ = [
    "BudgetBand",
    "DATASET_REVISION",
    "IngestionError",
    "REQUIRED_HF_COLUMNS",
    "Restaurant",
    "assert_hub_row_schema",
    "budget_band_from_cost",
    "iter_restaurants",
    "load_restaurants",
    "parse_approx_cost_two",
    "parse_cuisines",
    "parse_rating",
    "parse_votes",
    "parse_yes_no",
]
