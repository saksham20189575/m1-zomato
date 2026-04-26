"""
Phase 3 — integration layer: deterministic retrieval, ranking hint, prompt assembly.

Produces ``(candidates, prompt_payload)`` for Phase 4 without calling an LLM.
"""

from milestone1.phase3_integration.build import build_integration_output
from milestone1.phase3_integration.constants import (
    DEFAULT_CANDIDATE_CAP,
    MAX_CANDIDATE_CAP,
    MIN_CANDIDATE_CAP,
)
from milestone1.phase3_integration.filter import filter_and_rank
from milestone1.phase3_integration.model import IntegrationOutput, PromptPayload
from milestone1.phase3_integration.prompt import build_prompt_payload

__all__ = [
    "DEFAULT_CANDIDATE_CAP",
    "IntegrationOutput",
    "MAX_CANDIDATE_CAP",
    "MIN_CANDIDATE_CAP",
    "PromptPayload",
    "build_integration_output",
    "build_prompt_payload",
    "filter_and_rank",
]
