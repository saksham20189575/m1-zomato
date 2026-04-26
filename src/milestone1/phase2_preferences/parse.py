from __future__ import annotations

from typing import Any

from milestone1.phase1_ingestion.model import BudgetBand


def _strip_opt(value: Any) -> str | None:
    if value is None:
        return None
    s = str(value).strip()
    return s if s else None


def parse_budget_band(raw: Any) -> BudgetBand | None:
    """
    Parse user budget selection.

    ``None`` / empty means *no budget constraint* (any band).
    """
    if isinstance(raw, BudgetBand):
        if raw is BudgetBand.UNKNOWN:
            return None
        return raw
    s = _strip_opt(raw)
    if s is None:
        return None
    key = s.lower().replace(" ", "_")
    synonyms = {
        "low": BudgetBand.LOW,
        "cheap": BudgetBand.LOW,
        "budget": BudgetBand.LOW,
        "medium": BudgetBand.MEDIUM,
        "mid": BudgetBand.MEDIUM,
        "moderate": BudgetBand.MEDIUM,
        "high": BudgetBand.HIGH,
        "expensive": BudgetBand.HIGH,
        "luxury": BudgetBand.HIGH,
    }
    if key in synonyms:
        return synonyms[key]
    try:
        b = BudgetBand(s.lower())
    except ValueError:
        return None
    if b is BudgetBand.UNKNOWN:
        return None
    return b


def parse_minimum_rating(raw: Any) -> float | None:
    """Return ``None`` if absent or empty meaning *no minimum rating*."""
    if raw is None:
        return None
    if isinstance(raw, bool):
        raise ValueError("minimum_rating must be a number")
    if isinstance(raw, (int, float)):
        return float(raw)
    s = _strip_opt(raw)
    if s is None:
        return None
    try:
        return float(s)
    except ValueError:
        raise ValueError(f"minimum_rating is not a number: {raw!r}") from None


def parse_cuisine_list(raw: Any) -> tuple[str, ...]:
    """Accept list/tuple, comma/pipe-separated string, or single label."""
    if raw is None:
        return ()
    if isinstance(raw, (list, tuple)):
        out: list[str] = []
        for item in raw:
            s = _strip_opt(item)
            if s:
                out.append(s)
        return tuple(out)
    s = _strip_opt(raw)
    if s is None:
        return ()
    parts: list[str] = []
    for chunk in s.replace("|", ",").split(","):
        t = chunk.strip()
        if t:
            parts.append(t)
    return tuple(parts)
