"""Phase 6 — HTTP API defaults."""

from __future__ import annotations

# Comma-separated origins; browser must match one of these for credentialed/simple CORS.
DEFAULT_CORS_ORIGINS = (
    "http://127.0.0.1:5173",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://localhost:3000",
)

ENV_CORS_ORIGINS = "CORS_ORIGINS"

# Hub scan bound for POST /recommendations (avoid unbounded streaming).
DEFAULT_LOAD_LIMIT = 8_000
MIN_LOAD_LIMIT = 1
MAX_LOAD_LIMIT = 100_000

# Meta: cities list cap in JSON response.
DEFAULT_META_CITIES_CAP = 500
MIN_META_CITIES_CAP = 1
MAX_META_CITIES_CAP = 5_000
