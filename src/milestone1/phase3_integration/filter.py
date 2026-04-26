from __future__ import annotations

from collections.abc import Iterable

from milestone1.phase1_ingestion.model import BudgetBand, Restaurant
from milestone1.phase2_preferences.model import UserPreferences

# User budget is treated as a maximum spend band: restaurants at or below that tier match.
_ALLOWED_RESTAURANT_BANDS: dict[BudgetBand, frozenset[BudgetBand]] = {
    BudgetBand.LOW: frozenset({BudgetBand.LOW, BudgetBand.UNKNOWN}),
    BudgetBand.MEDIUM: frozenset({BudgetBand.LOW, BudgetBand.MEDIUM, BudgetBand.UNKNOWN}),
    BudgetBand.HIGH: frozenset(
        {BudgetBand.LOW, BudgetBand.MEDIUM, BudgetBand.HIGH, BudgetBand.UNKNOWN}
    ),
}


def _budget_ok(prefs: UserPreferences, r: Restaurant) -> bool:
    if prefs.budget_band is None:
        return True
    allowed = _ALLOWED_RESTAURANT_BANDS.get(prefs.budget_band)
    if allowed is None:
        return True
    return r.budget_band in allowed


def _rating_ok(prefs: UserPreferences, r: Restaurant) -> bool:
    if prefs.minimum_rating is None:
        return True
    if r.rating is None:
        return False
    return r.rating >= prefs.minimum_rating


def _location_ok(prefs: UserPreferences, r: Restaurant) -> bool:
    target = prefs.location.casefold()
    if r.city and r.city.casefold() == target:
        return True
    if r.neighborhood and r.neighborhood.casefold() == target:
        return True
    return False


def _cuisine_ok(prefs: UserPreferences, r: Restaurant) -> bool:
    if not prefs.cuisines:
        return True
    rest = {c.casefold() for c in r.cuisines}
    return any(u.casefold() in rest for u in prefs.cuisines)


def _hard_filter(prefs: UserPreferences, r: Restaurant) -> bool:
    return (
        _location_ok(prefs, r)
        and _rating_ok(prefs, r)
        and _budget_ok(prefs, r)
        and _cuisine_ok(prefs, r)
    )


def _rank_key(r: Restaurant) -> tuple:
    """
    Sort key: higher rating first, then more votes, then stable id.

    Rows with missing rating sort after those with a score (tuple ordering).
    """
    has_rating = r.rating is not None
    rating = -(r.rating or 0.0)
    votes = -(r.votes or 0)
    return (not has_rating, rating, votes, r.id)


def filter_and_rank(
    restaurants: Iterable[Restaurant],
    prefs: UserPreferences,
    *,
    cap: int,
) -> tuple[tuple[Restaurant, ...], int]:
    """
    Apply hard filters, pre-sort for LLM context, then cap.

    Returns ``(candidates, matched_count)`` where ``matched_count`` is before capping.
    """
    matched = [r for r in restaurants if _hard_filter(prefs, r)]
    matched_count = len(matched)
    matched.sort(key=_rank_key)
    if cap < 1:
        return (), matched_count
    return tuple(matched[:cap]), matched_count
