from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class BudgetBand(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class Restaurant:
    """Canonical restaurant row after Phase 1 normalization."""

    id: str
    name: str
    city: str
    neighborhood: str
    address: str
    cuisines: tuple[str, ...]
    rating: float | None
    approx_cost_two: int | None
    approx_cost_two_raw: str | None
    budget_band: BudgetBand
    votes: int | None
    restaurant_type: str | None
    listing_type: str | None
    online_order: bool | None
    book_table: bool | None
    menu_sample: str | None
    dishes_liked: str | None
    url: str | None
    phone: str | None
