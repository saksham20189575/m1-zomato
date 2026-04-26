"""
Phase 4 — Groq-backed recommendation engine: chat completion, JSON parse, fallback.
"""

from milestone1.phase4_llm.constants import (
    DEFAULT_GROQ_MODEL,
    DEFAULT_MAX_RETRIES,
    DEFAULT_MAX_TOKENS,
    DEFAULT_TEMPERATURE,
    DEFAULT_TIMEOUT_SEC,
    DEFAULT_TOP_K,
    GROQ_CHAT_COMPLETIONS_URL,
)
from milestone1.phase4_llm.errors import GroqTransportError, RankingsParseError
from milestone1.phase4_llm.fallback import deterministic_fallback_rankings
from milestone1.phase4_llm.groq_client import GroqCompletion, complete_chat, complete_chat_json_relaxed
from milestone1.phase4_llm.model import RankedRecommendation, RecommendResult
from milestone1.phase4_llm.parse import parse_rankings_json, parse_rankings_json_lenient
from milestone1.phase4_llm.recommend import recommend_with_groq

__all__ = [
    "DEFAULT_GROQ_MODEL",
    "DEFAULT_MAX_RETRIES",
    "DEFAULT_MAX_TOKENS",
    "DEFAULT_TEMPERATURE",
    "DEFAULT_TIMEOUT_SEC",
    "DEFAULT_TOP_K",
    "GROQ_CHAT_COMPLETIONS_URL",
    "GroqCompletion",
    "GroqTransportError",
    "RankedRecommendation",
    "RankingsParseError",
    "RecommendResult",
    "complete_chat",
    "complete_chat_json_relaxed",
    "deterministic_fallback_rankings",
    "parse_rankings_json",
    "parse_rankings_json_lenient",
    "recommend_with_groq",
]
