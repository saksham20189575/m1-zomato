from __future__ import annotations

import os
import time
from collections.abc import Callable, Iterable

from milestone1.phase1_ingestion.model import Restaurant
from milestone1.phase2_preferences.model import UserPreferences
from milestone1.phase3_integration.build import build_integration_output
from milestone1.phase3_integration.constants import DEFAULT_CANDIDATE_CAP
from milestone1.phase3_integration.model import PromptPayload

from milestone1.phase4_llm.constants import (
    DEFAULT_GROQ_MODEL,
    DEFAULT_MAX_RETRIES,
    DEFAULT_MAX_TOKENS,
    DEFAULT_TEMPERATURE,
    DEFAULT_TIMEOUT_SEC,
    DEFAULT_TOP_K,
)
from milestone1.phase4_llm.errors import GroqTransportError, RankingsParseError
from milestone1.phase4_llm.fallback import deterministic_fallback_rankings
from milestone1.phase4_llm.groq_client import GroqCompletion, complete_chat_json_relaxed
from milestone1.phase4_llm.model import RankedRecommendation, RecommendResult
from milestone1.phase4_llm.parse import parse_rankings_json

GroqCaller = Callable[[PromptPayload], GroqCompletion]


def _augment_prompt_for_top_k(prompt: PromptPayload, top_k: int) -> PromptPayload:
    """Ask the model for up to ``top_k`` grounded rows (Phase 3 table stays unchanged)."""
    if top_k < 1:
        return prompt
    suffix = (
        f"\n## Requested result size\n"
        f"Include up to {top_k} restaurants in `rankings` (fewer only if there are not "
        "enough suitable matches). Use consecutive ranks 1 through N with no gaps.\n"
    )
    return PromptPayload(
        system_message=prompt.system_message,
        user_message=prompt.user_message + suffix,
    )


def _enrich(
    triples: tuple[tuple[str, int, str], ...],
    by_id: dict[str, Restaurant],
) -> tuple[RankedRecommendation, ...]:
    out: list[RankedRecommendation] = []
    for rid, rank, expl in triples:
        out.append(
            RankedRecommendation(
                restaurant_id=rid,
                rank=rank,
                explanation=expl,
                restaurant=by_id.get(rid),
            )
        )
    return tuple(out)


def _top_k_slice(
    items: tuple[RankedRecommendation, ...],
    top_k: int,
) -> tuple[RankedRecommendation, ...]:
    if top_k < 1:
        return ()
    return tuple(sorted(items, key=lambda x: (x.rank, x.restaurant_id))[:top_k])


def recommend_with_groq(
    restaurants: Iterable[Restaurant],
    prefs: UserPreferences,
    *,
    candidate_cap: int = DEFAULT_CANDIDATE_CAP,
    top_k: int = DEFAULT_TOP_K,
    api_key: str | None = None,
    model: str | None = None,
    temperature: float = DEFAULT_TEMPERATURE,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    timeout_sec: float = DEFAULT_TIMEOUT_SEC,
    max_retries: int = DEFAULT_MAX_RETRIES,
    groq_caller: GroqCaller | None = None,
) -> RecommendResult:
    """
    Phase 4 pipeline: integrate (Phase 3), call Groq, parse JSON, or deterministic fallback.
    """
    key = api_key if api_key is not None else os.environ.get("GROQ_API_KEY", "")
    mdl = model if model is not None else os.environ.get("GROQ_MODEL", DEFAULT_GROQ_MODEL)

    integration = build_integration_output(restaurants, prefs, candidate_cap=candidate_cap)
    matched = integration.matched_count
    cands: tuple[Restaurant, ...] = integration.candidates
    n = len(cands)

    if not cands:
        return RecommendResult(
            source="no_candidates",
            rankings=(),
            matched_count=matched,
            candidate_count=0,
            usage=None,
            latency_ms=None,
            detail="No restaurants matched the hard filters.",
        )

    by_id = {r.id: r for r in cands}
    allowed = frozenset(by_id.keys())

    caller = groq_caller
    if caller is None:
        def _default_caller(p: PromptPayload) -> GroqCompletion:
            return complete_chat_json_relaxed(
                p,
                api_key=key,
                model=mdl,
                temperature=temperature,
                max_tokens=max_tokens,
                timeout_sec=timeout_sec,
                max_retries=max_retries,
            )

        caller = _default_caller

    prompt = _augment_prompt_for_top_k(integration.prompt, top_k)

    t0 = time.perf_counter()
    try:
        completion = caller(prompt)
    except GroqTransportError as e:
        fb = deterministic_fallback_rankings(cands, top_k=top_k)
        return RecommendResult(
            source="fallback",
            rankings=fb,
            matched_count=matched,
            candidate_count=n,
            usage=None,
            latency_ms=(time.perf_counter() - t0) * 1000.0,
            detail=str(e),
        )

    latency_ms = (time.perf_counter() - t0) * 1000.0

    try:
        triples = parse_rankings_json(completion.text, allowed)
    except RankingsParseError:
        fb = deterministic_fallback_rankings(cands, top_k=top_k)
        return RecommendResult(
            source="fallback",
            rankings=fb,
            matched_count=matched,
            candidate_count=n,
            usage=completion.usage,
            latency_ms=latency_ms,
            detail="Model output failed rankings JSON validation.",
        )

    enriched = _enrich(triples, by_id)
    sliced = _top_k_slice(enriched, top_k)

    return RecommendResult(
        source="llm",
        rankings=sliced,
        matched_count=matched,
        candidate_count=n,
        usage=completion.usage,
        latency_ms=latency_ms,
        detail=None,
    )
