"""Phase 0 frozen scope — single source for CLI ``info`` output and tests."""

# End users submit preferences and read recommendations here (implemented in later phases).
USER_INPUT_SURFACE = "web_ui"

# Operator/developer entry point (info, doctor); not the primary product surface.
DEV_CLI = "milestone1"

PYTHON_MIN = (3, 11)

DATASET_ID = "ManikaSaini/zomato-restaurant-recommendation"
DATASET_SPLIT = "train"

# Preference fields planned for v1 (see docs/phase0-scope.md).
PREFERENCE_FIELDS_V1 = (
    "location",
    "budget",
    "cuisine",
    "minimum_rating",
    "additional_preferences",
)
