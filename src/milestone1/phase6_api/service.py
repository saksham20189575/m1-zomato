from __future__ import annotations

import logging
import os

from milestone1.phase1_ingestion import load_restaurants
from milestone1.phase2_preferences import allowed_locations_from_restaurants, preferences_from_mapping
from milestone1.phase4_llm.constants import DEFAULT_GROQ_MODEL
from milestone1.phase4_llm.model import RankedRecommendation, RecommendResult
from milestone1.phase4_llm.recommend import recommend_with_groq

from milestone1.phase6_api.constants import DEFAULT_LOAD_LIMIT, MAX_META_CITIES_CAP, MIN_META_CITIES_CAP
from milestone1.phase6_api.schemas import MetaResponse, RankingDTO, RecommendRequest, RecommendResponse, RestaurantDTO

log = logging.getLogger("milestone1.phase6_api")


def _resolved_model(explicit: str | None) -> str:
    return explicit if explicit else os.environ.get("GROQ_MODEL", DEFAULT_GROQ_MODEL)


def _ranking_to_dto(r: RankedRecommendation) -> RankingDTO:
    rest = r.restaurant
    if rest is None:
        return RankingDTO(
            rank=r.rank,
            restaurant_id=r.restaurant_id,
            explanation=r.explanation,
            restaurant=None,
        )
    dto = RestaurantDTO(
        id=rest.id,
        name=rest.name,
        city=rest.city,
        cuisines=list(rest.cuisines),
        rating=rest.rating,
        approx_cost_two_inr=rest.approx_cost_two,
        budget_band=rest.budget_band.value,
    )
    return RankingDTO(
        rank=r.rank,
        restaurant_id=r.restaurant_id,
        explanation=r.explanation,
        restaurant=dto,
    )


def recommend_to_response(req: RecommendRequest) -> RecommendResponse:
    load_lim = req.load_limit if req.load_limit is not None else DEFAULT_LOAD_LIMIT
    rows = load_restaurants(limit=load_lim, dedupe=True)
    allowed = sorted(allowed_locations_from_restaurants(rows))

    payload: dict[str, object] = {
        "location": req.location,
        "budget": req.budget,
        "minimum_rating": req.minimum_rating,
        "additional_preferences": req.additional_preferences,
    }
    if req.cuisines:
        payload["cuisines"] = req.cuisines

    prefs = preferences_from_mapping(payload, allowed_city_names=allowed)
    model = _resolved_model(req.model)
    result = recommend_with_groq(
        rows,
        prefs,
        candidate_cap=req.candidate_cap,
        top_k=req.top_k,
        model=req.model,
        temperature=req.temperature,
        max_tokens=req.max_tokens,
        timeout_sec=req.timeout,
    )
    log.info(
        "recommendation_completed source=%s matched=%s candidate=%s rankings=%s latency_ms=%s "
        "prompt_tokens=%s completion_tokens=%s",
        result.source,
        result.matched_count,
        result.candidate_count,
        len(result.rankings),
        result.latency_ms,
        (result.usage or {}).get("prompt_tokens"),
        (result.usage or {}).get("completion_tokens"),
    )
    return _result_to_response(result, model)


def _result_to_response(result: RecommendResult, model: str) -> RecommendResponse:
    usage: dict[str, int] | None = None
    if result.usage:
        usage = {k: int(v) for k, v in result.usage.items() if isinstance(v, (int, float))}
    return RecommendResponse(
        source=result.source,
        matched_count=result.matched_count,
        candidate_count=result.candidate_count,
        latency_ms=result.latency_ms,
        usage=usage,
        detail=result.detail,
        model=model,
        rankings=[_ranking_to_dto(r) for r in result.rankings],
    )


_locations_cache: dict[int, list[str]] = {}


def _locations_for_load_limit(load_limit: int) -> list[str]:
    cached = _locations_cache.get(load_limit)
    if cached is not None:
        return cached
    rows = load_restaurants(limit=load_limit, dedupe=True)
    locations = sorted(allowed_locations_from_restaurants(rows))
    _locations_cache[load_limit] = locations
    return locations


def prewarm_locations(load_limit: int) -> int:
    """Populate the in-process locations cache; returns count of cached entries."""
    return len(_locations_for_load_limit(load_limit))


def meta_cities(*, load_limit: int, cities_cap: int) -> MetaResponse:
    cap = max(MIN_META_CITIES_CAP, min(cities_cap, MAX_META_CITIES_CAP))
    locations = _locations_for_load_limit(load_limit)
    truncated = len(locations) > cap
    return MetaResponse(
        cities=list(locations[:cap]),
        truncated=truncated,
        load_limit_used=load_limit,
        cities_cap=cap,
    )


def groq_configured() -> bool:
    return bool(os.environ.get("GROQ_API_KEY", "").strip())
