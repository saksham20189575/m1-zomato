from __future__ import annotations

from pydantic import BaseModel, Field

from milestone1.phase2_preferences.constants import MAX_ADDITIONAL_PREFERENCE_CHARS
from milestone1.phase3_integration.constants import (
    DEFAULT_CANDIDATE_CAP,
    MAX_CANDIDATE_CAP,
    MIN_CANDIDATE_CAP,
)
from milestone1.phase4_llm.constants import (
    DEFAULT_MAX_TOKENS,
    DEFAULT_TEMPERATURE,
    DEFAULT_TIMEOUT_SEC,
    DEFAULT_TOP_K,
)
from milestone1.phase6_api.constants import MAX_LOAD_LIMIT, MIN_LOAD_LIMIT


class RecommendRequest(BaseModel):
    """JSON body aligned with Phase 2 ``preferences_from_mapping`` keys + run tuning."""

    location: str = Field(..., min_length=1)
    budget: str | None = None
    cuisines: list[str] | None = None
    minimum_rating: float | None = None
    additional_preferences: str | None = Field(None, max_length=MAX_ADDITIONAL_PREFERENCE_CHARS)
    load_limit: int | None = Field(
        default=None,
        ge=MIN_LOAD_LIMIT,
        le=MAX_LOAD_LIMIT,
        description="Max Hub rows to scan (default from server if omitted).",
    )
    candidate_cap: int = Field(default=DEFAULT_CANDIDATE_CAP, ge=MIN_CANDIDATE_CAP, le=MAX_CANDIDATE_CAP)
    top_k: int = Field(default=DEFAULT_TOP_K, ge=1, le=50)
    model: str | None = None
    temperature: float = Field(default=DEFAULT_TEMPERATURE, ge=0.0, le=2.0)
    max_tokens: int = Field(default=DEFAULT_MAX_TOKENS, ge=64, le=8192)
    timeout: float = Field(default=DEFAULT_TIMEOUT_SEC, ge=5.0, le=300.0)


class RestaurantDTO(BaseModel):
    id: str
    name: str
    city: str
    cuisines: list[str]
    rating: float | None
    approx_cost_two_inr: int | None
    budget_band: str


class RankingDTO(BaseModel):
    rank: int
    restaurant_id: str
    explanation: str
    restaurant: RestaurantDTO | None


class RecommendResponse(BaseModel):
    source: str
    matched_count: int
    candidate_count: int
    latency_ms: float | None
    usage: dict[str, int] | None
    detail: str | None
    model: str
    rankings: list[RankingDTO]


class HealthResponse(BaseModel):
    status: str
    groq_configured: bool


class MetaResponse(BaseModel):
    cities: list[str]
    truncated: bool
    load_limit_used: int
    cities_cap: int
