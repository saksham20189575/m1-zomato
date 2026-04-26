from __future__ import annotations

from collections.abc import Sequence

from milestone1.phase1_ingestion.model import Restaurant

from milestone1.phase4_llm.model import RankedRecommendation


def deterministic_fallback_rankings(
    candidates: Sequence[Restaurant],
    *,
    top_k: int,
) -> tuple[RankedRecommendation, ...]:
    """
    Deterministic top-*k* with template explanations when the LLM fails or output is unusable.
    """
    if top_k < 1:
        return ()
    out: list[RankedRecommendation] = []
    for i, r in enumerate(candidates[:top_k], start=1):
        expl = (
            "Automated fallback: ranked from filter match and pre-sort (rating, votes) "
            f"because the model response was missing or invalid (rank {i})."
        )
        out.append(
            RankedRecommendation(
                restaurant_id=r.id,
                rank=i,
                explanation=expl,
                restaurant=r,
            )
        )
    return tuple(out)
