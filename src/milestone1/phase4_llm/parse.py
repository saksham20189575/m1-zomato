from __future__ import annotations

import json
from collections.abc import Mapping

from milestone1.phase4_llm.errors import RankingsParseError


def _strip_markdown_fences(text: str) -> str:
    t = text.strip()
    if not t.startswith("```"):
        return t
    lines = t.splitlines()
    if not lines:
        return t
    # Drop opening ``` or ```json
    lines = lines[1:]
    while lines and lines[-1].strip() == "```":
        lines = lines[:-1]
    return "\n".join(lines).strip()


def _extract_json_object(text: str) -> str:
    t = _strip_markdown_fences(text)
    start = t.find("{")
    end = t.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise RankingsParseError("No JSON object found in model output.")
    return t[start : end + 1]


def _as_str(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise RankingsParseError(f"{field} must be a string.")
    s = value.strip()
    if not s:
        raise RankingsParseError(f"{field} must be non-empty.")
    return s


def _as_int(value: object, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise RankingsParseError(f"{field} must be an integer.")
    return int(value)


def parse_rankings_json(
    raw_text: str,
    allowed_ids: frozenset[str],
) -> tuple[tuple[str, int, str], ...]:
    """
    Parse and validate ``rankings`` from model output.

    Returns tuples ``(restaurant_id, rank, explanation)`` sorted by ``rank`` ascending.
    Drops entries with unknown ``restaurant_id`` or invalid shape; duplicate ids keep
    the lowest rank entry.
    """
    try:
        obj = json.loads(_extract_json_object(raw_text))
    except json.JSONDecodeError as e:
        raise RankingsParseError(f"Invalid JSON: {e}") from e

    if not isinstance(obj, Mapping):
        raise RankingsParseError("Top-level JSON must be an object.")
    raw_list = obj.get("rankings")
    if raw_list is None:
        raise RankingsParseError("Missing 'rankings' array.")
    if not isinstance(raw_list, list):
        raise RankingsParseError("'rankings' must be an array.")

    best: dict[str, tuple[int, str]] = {}
    for i, item in enumerate(raw_list):
        if not isinstance(item, Mapping):
            continue
        try:
            rid = _as_str(item.get("restaurant_id"), "restaurant_id")
            rank = _as_int(item.get("rank"), "rank")
            expl = _as_str(item.get("explanation"), "explanation")
        except RankingsParseError:
            continue
        if rid not in allowed_ids:
            continue
        if rank < 1:
            continue
        prev = best.get(rid)
        if prev is None or rank < prev[0]:
            best[rid] = (rank, expl)

    if not best:
        return ()

    ordered = sorted(best.items(), key=lambda kv: (kv[1][0], kv[0]))
    return tuple((rid, rank, expl) for rid, (rank, expl) in ordered)


def parse_rankings_json_lenient(
    raw_text: str,
    allowed_ids: frozenset[str],
) -> tuple[tuple[str, int, str], ...]:
    """
    Like ``parse_rankings_json`` but returns ``()`` instead of raising on top-level
    structural problems, so callers can fall back when the model returns non-JSON prose.
    """
    try:
        return parse_rankings_json(raw_text, allowed_ids)
    except RankingsParseError:
        return ()
