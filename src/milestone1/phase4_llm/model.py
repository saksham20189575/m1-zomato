from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from milestone1.phase1_ingestion.model import Restaurant


@dataclass(frozen=True, slots=True)
class RankedRecommendation:
    """One ranked row ready for Phase 5 display."""

    restaurant_id: str
    rank: int
    explanation: str
    restaurant: Restaurant | None


RecommendSource = Literal["llm", "fallback", "no_candidates"]


@dataclass(frozen=True, slots=True)
class RecommendResult:
    """End-to-end recommendation output (Phase 4 exit artifact)."""

    source: RecommendSource
    rankings: tuple[RankedRecommendation, ...]
    matched_count: int
    candidate_count: int
    usage: dict[str, int] | None
    latency_ms: float | None
    detail: str | None
    """Human-readable note (e.g. why fallback ran)."""
