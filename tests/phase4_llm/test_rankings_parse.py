from __future__ import annotations

import pytest

from milestone1.phase4_llm.errors import RankingsParseError
from milestone1.phase4_llm.parse import parse_rankings_json, parse_rankings_json_lenient


def test_parse_rankings_basic_order() -> None:
    allowed = frozenset({"a", "b"})
    raw = '{"rankings": [{"restaurant_id": "b", "rank": 2, "explanation": "y"}, {"restaurant_id": "a", "rank": 1, "explanation": "x"}]}'
    out = parse_rankings_json(raw, allowed)
    assert [t[0] for t in out] == ["a", "b"]
    assert [t[1] for t in out] == [1, 2]


def test_parse_strips_markdown_fence() -> None:
    allowed = frozenset({"x"})
    raw = '```json\n{"rankings": [{"restaurant_id": "x", "rank": 1, "explanation": "ok"}]}\n```'
    out = parse_rankings_json(raw, allowed)
    assert len(out) == 1


def test_parse_drops_unknown_ids() -> None:
    allowed = frozenset({"a"})
    raw = '{"rankings": [{"restaurant_id": "nope", "rank": 1, "explanation": "bad"}]}'
    assert parse_rankings_json(raw, allowed) == ()


def test_parse_duplicate_id_keeps_best_rank() -> None:
    allowed = frozenset({"a"})
    raw = (
        '{"rankings": ['
        '{"restaurant_id": "a", "rank": 5, "explanation": "late"},'
        '{"restaurant_id": "a", "rank": 1, "explanation": "early"}'
        "]}"
    )
    out = parse_rankings_json(raw, allowed)
    assert out == (("a", 1, "early"),)


def test_parse_raises_on_missing_rankings() -> None:
    with pytest.raises(RankingsParseError):
        parse_rankings_json("{}", frozenset({"a"}))


def test_parse_lenient_returns_empty_on_bad_json() -> None:
    assert parse_rankings_json_lenient("not json", frozenset()) == ()
