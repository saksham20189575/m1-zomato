from __future__ import annotations

import json

from milestone1.phase4_llm.model import RecommendResult
from milestone1.phase5_output.observability import recommendation_telemetry_doc


def test_telemetry_has_counts_no_free_text() -> None:
    res = RecommendResult(
        source="llm",
        rankings=(),
        matched_count=3,
        candidate_count=2,
        usage={"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
        latency_ms=99.5,
        detail=None,
    )
    doc = recommendation_telemetry_doc(res)
    assert doc["event"] == "recommendation_completed"
    assert doc["matched_count"] == 3
    assert doc["candidate_count"] == 2
    assert doc["ranking_count"] == 0
    assert doc["prompt_tokens"] == 10
    assert "Bellandur" not in json.dumps(doc)
