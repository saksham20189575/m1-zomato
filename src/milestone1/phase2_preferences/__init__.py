"""
Phase 2 — user preference model and validation.

Produces ``UserPreferences`` for the Phase 3 filter layer.
"""

from milestone1.phase2_preferences.build import (
    allowed_cities_from_restaurants,
    allowed_locations_from_restaurants,
    preferences_from_mapping,
)
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

__all__ = [
    "MAX_ADDITIONAL_PREFERENCE_CHARS",
    "RATING_MAX",
    "RATING_MIN",
    "PreferencesValidationError",
    "UserPreferences",
    "allowed_cities_from_restaurants",
    "allowed_locations_from_restaurants",
    "parse_budget_band",
    "parse_cuisine_list",
    "parse_minimum_rating",
    "preferences_from_mapping",
]
