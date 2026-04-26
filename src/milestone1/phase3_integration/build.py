from __future__ import annotations

from collections.abc import Iterable

from milestone1.phase1_ingestion.model import Restaurant
from milestone1.phase2_preferences.model import UserPreferences

from milestone1.phase3_integration.constants import DEFAULT_CANDIDATE_CAP
from milestone1.phase3_integration.filter import filter_and_rank
from milestone1.phase3_integration.model import IntegrationOutput
from milestone1.phase3_integration.prompt import build_prompt_payload


def build_integration_output(
    restaurants: Iterable[Restaurant],
    prefs: UserPreferences,
    *,
    candidate_cap: int = DEFAULT_CANDIDATE_CAP,
) -> IntegrationOutput:
    """
    Given preferences and a restaurant corpus, produce capped candidates and prompt text.

    This is the Phase 3 exit artifact: no LLM calls.
    """
    candidates, matched_count = filter_and_rank(restaurants, prefs, cap=candidate_cap)
    prompt = build_prompt_payload(prefs, candidates)
    return IntegrationOutput(
        candidates=candidates,
        matched_count=matched_count,
        prompt=prompt,
    )
