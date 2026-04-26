from __future__ import annotations

from dataclasses import dataclass

from milestone1.phase1_ingestion.model import Restaurant


@dataclass(frozen=True, slots=True)
class PromptPayload:
    """Messages ready for an LLM client (Phase 4); no network I/O here."""

    system_message: str
    user_message: str


@dataclass(frozen=True, slots=True)
class IntegrationOutput:
    """Stable ``(candidates, prompt)`` bundle without calling the LLM."""

    candidates: tuple[Restaurant, ...]
    """Ranked, length-capped list passed to the prompt."""

    matched_count: int
    """Count of rows passing hard filters before the cap."""

    prompt: PromptPayload
