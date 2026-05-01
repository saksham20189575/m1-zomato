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
# ``DEFAULT_LOAD_LIMIT`` is a compile-time fallback; the API resolves the
# effective value at request time via ``effective_default_load_limit()``,
# which honors the ``LOAD_LIMIT`` env (see ``service.py``). Lower it when
# running on a memory-constrained host (e.g. ``LOAD_LIMIT=3000``).
DEFAULT_LOAD_LIMIT = 8_000
MIN_LOAD_LIMIT = 1
MAX_LOAD_LIMIT = 100_000

ENV_LOAD_LIMIT = "LOAD_LIMIT"

# Background prewarm (locations cache) at app startup. Disable via
# ``PREWARM=0`` to keep boot RSS small on tight tiers; the first
# ``/api/v1/meta`` call will load on demand.
ENV_PREWARM = "PREWARM"

# Meta: cities list cap in JSON response.
DEFAULT_META_CITIES_CAP = 500
MIN_META_CITIES_CAP = 1
MAX_META_CITIES_CAP = 5_000
