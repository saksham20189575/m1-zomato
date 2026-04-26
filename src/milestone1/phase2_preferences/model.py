from __future__ import annotations

from dataclasses import dataclass

from milestone1.phase1_ingestion.model import BudgetBand


@dataclass(frozen=True, slots=True)
class UserPreferences:
    """Normalized user input for Phase 3 filtering and prompting."""

    location: str
    budget_band: BudgetBand | None
    cuisines: tuple[str, ...]
    minimum_rating: float | None
    additional_preferences: str | None
