from __future__ import annotations

import json
import sys
from typing import Any, TextIO

from milestone1.phase4_llm.model import RecommendResult


def recommendation_telemetry_doc(result: RecommendResult) -> dict[str, Any]:
    """
    Structured metrics safe for logs (no user free-text, no addresses, no API keys).

    Includes aggregate filter/model counts only.
    """
    usage = result.usage or {}
    out: dict[str, Any] = {
        "event": "recommendation_completed",
        "source": result.source,
        "matched_count": result.matched_count,
        "candidate_count": result.candidate_count,
        "ranking_count": len(result.rankings),
        "latency_ms": result.latency_ms,
    }
    for k in ("prompt_tokens", "completion_tokens", "total_tokens"):
        if k in usage:
            try:
                out[k] = int(usage[k])  # type: ignore[arg-type]
            except (TypeError, ValueError):
                continue
    if result.detail:
        out["detail_present"] = True
    return out


def emit_recommendation_telemetry(
    result: RecommendResult,
    *,
    stream: TextIO | None = None,
) -> None:
    """Write one JSON line of telemetry (default: stderr)."""
    stream = stream if stream is not None else sys.stderr
    stream.write(json.dumps(recommendation_telemetry_doc(result), sort_keys=True) + "\n")
