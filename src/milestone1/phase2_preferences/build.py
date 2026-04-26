from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from milestone1.phase1_ingestion.model import Restaurant
from milestone1.phase2_preferences.constants import (
    MAX_ADDITIONAL_PREFERENCE_CHARS,
    RATING_MAX,
    RATING_MIN,
)
from milestone1.phase2_preferences.errors import PreferencesValidationError
from milestone1.phase2_preferences.model import UserPreferences
from milestone1.phase2_preferences.parse import (
    parse_budget_band,
    parse_cuisine_list,
    parse_minimum_rating,
)


def _canon_city_set(allowed_city_names: Iterable[str]) -> dict[str, str]:
    """Map casefolded city -> canonical spelling from corpus."""
    m: dict[str, str] = {}
    for c in allowed_city_names:
        s = str(c).strip()
        if not s:
            continue
        m[s.casefold()] = s
    return m


def preferences_from_mapping(
    data: Mapping[str, Any],
    *,
    allowed_city_names: Iterable[str] | None = None,
) -> UserPreferences:
    """
    Build ``UserPreferences`` from form-like keys (web) or a plain dict (tests).

    Recognized keys (first match wins per group):
    - ``location`` (required)
    - ``budget`` / ``budget_band``
    - ``cuisines`` / ``cuisine`` (string or sequence; empty = any cuisine)
    - ``minimum_rating`` / ``min_rating``
    - ``additional_preferences`` / ``additional`` / ``notes``

    If ``allowed_city_names`` is provided, ``location`` must match one city
    (case-insensitive). Otherwise only non-empty checks apply.
    """
    errors: list[tuple[str, str]] = []

    loc_raw = _first(data, ("location", "city", "listed_in(city)"))
    location = str(loc_raw).strip() if loc_raw is not None else ""
    if not location:
        errors.append(("location", "Location is required."))

    budget_raw = _first(data, ("budget_band", "budget"))
    budget_parsed = parse_budget_band(budget_raw)
    if _is_meaningful_scalar(budget_raw) and budget_parsed is None:
        errors.append(
            ("budget",
             "Invalid budget. Use low, medium, high, or leave empty for any budget."))

    cuisine_raw = _first(data, ("cuisines", "cuisine"))
    cuisines = parse_cuisine_list(cuisine_raw)

    min_raw = _first(data, ("minimum_rating", "min_rating", "rating_min"))
    minimum_rating: float | None
    if isinstance(min_raw, (list, dict)):
        errors.append(("minimum_rating", "Minimum rating must be a single number."))
        minimum_rating = None
    else:
        try:
            minimum_rating = parse_minimum_rating(min_raw)
        except ValueError:
            errors.append(("minimum_rating", "Minimum rating must be a number."))
            minimum_rating = None

    if minimum_rating is not None:
        if minimum_rating < RATING_MIN or minimum_rating > RATING_MAX:
            errors.append(
                ("minimum_rating",
                 f"Minimum rating must be between {RATING_MIN:g} and {RATING_MAX:g}."))

    add_raw = _first(data, ("additional_preferences", "additional", "notes"))
    additional: str | None
    if add_raw is None:
        additional = None
    else:
        additional = str(add_raw).strip() or None
    if additional is not None and len(additional) > MAX_ADDITIONAL_PREFERENCE_CHARS:
        errors.append(
            ("additional_preferences",
             f"Additional preferences must be at most {MAX_ADDITIONAL_PREFERENCE_CHARS} characters."))

    if errors:
        raise PreferencesValidationError(errors)

    assert location

    if allowed_city_names is not None:
        canon = _canon_city_set(allowed_city_names)
        key = location.casefold()
        if key not in canon:
            errors.append(
                ("location",
                 "Unknown location. Choose a city that exists in the loaded dataset."))
            raise PreferencesValidationError(errors)
        location = canon[key]

    return UserPreferences(
        location=location,
        budget_band=budget_parsed,
        cuisines=cuisines,
        minimum_rating=minimum_rating,
        additional_preferences=additional,
    )


def _first(data: Mapping[str, Any], keys: tuple[str, ...]) -> Any:
    for k in keys:
        if k in data:
            return data[k]
    return None


def _is_meaningful_scalar(raw: Any) -> bool:
    if raw is None:
        return False
    if isinstance(raw, str):
        return bool(raw.strip())
    if isinstance(raw, (list, tuple, dict)) and not raw:
        return False
    return True


def allowed_cities_from_restaurants(restaurants: Iterable[Restaurant]) -> frozenset[str]:
    """Extract unique ``city`` values from Phase 1 ``Restaurant`` rows."""
    cities: set[str] = set()
    for r in restaurants:
        city = getattr(r, "city", None)
        if city and str(city).strip():
            cities.add(str(city).strip())
    return frozenset(cities)


def allowed_locations_from_restaurants(restaurants: Iterable[Restaurant]) -> frozenset[str]:
    """Union of ``city`` and ``neighborhood`` values; the broader pickable set for UIs."""
    locations: set[str] = set()
    for r in restaurants:
        for attr in ("city", "neighborhood"):
            v = getattr(r, attr, None)
            if v and str(v).strip():
                locations.add(str(v).strip())
    return frozenset(locations)
