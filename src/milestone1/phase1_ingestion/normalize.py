from __future__ import annotations

import hashlib
import re
from typing import Any

from milestone1.phase1_ingestion.constants import BUDGET_LOW_MAX_INR, BUDGET_MEDIUM_MAX_INR
from milestone1.phase1_ingestion.model import BudgetBand


def _strip_str(value: Any) -> str | None:
    if value is None:
        return None
    s = str(value).strip()
    return s if s else None


def parse_rating(raw: Any) -> float | None:
    """Parse Zomato-style rating strings to a float, or None if unknown."""
    s = _strip_str(raw)
    if s is None:
        return None
    upper = s.upper()
    if upper in {"-", "NEW", "NAN", "NONE", ""}:
        return None
    m = re.match(r"^\s*(\d+(?:\.\d+)?)\s*(?:/\s*5)?\s*$", s)
    if m:
        return float(m.group(1))
    try:
        return float(s)
    except ValueError:
        return None


def parse_approx_cost_two(raw: Any) -> tuple[int | None, str | None]:
    """Return (parsed_inr, raw_display). Digits are extracted from messy strings."""
    s = _strip_str(raw)
    if s is None:
        return None, None
    digits = re.sub(r"[^\d]", "", s)
    if not digits:
        return None, s
    try:
        return int(digits), s
    except ValueError:
        return None, s


def budget_band_from_cost(cost_inr: int | None) -> BudgetBand:
    if cost_inr is None:
        return BudgetBand.UNKNOWN
    if cost_inr <= BUDGET_LOW_MAX_INR:
        return BudgetBand.LOW
    if cost_inr <= BUDGET_MEDIUM_MAX_INR:
        return BudgetBand.MEDIUM
    return BudgetBand.HIGH


def parse_cuisines(raw: Any) -> tuple[str, ...]:
    s = _strip_str(raw)
    if s is None:
        return ()
    parts = re.split(r"[|,]", s)
    out: list[str] = []
    for p in parts:
        t = p.strip()
        if t:
            out.append(t)
    return tuple(out)


def parse_votes(raw: Any) -> int | None:
    s = _strip_str(raw)
    if s is None:
        return None
    try:
        return int(float(s))
    except ValueError:
        return None


def parse_yes_no(raw: Any) -> bool | None:
    s = _strip_str(raw)
    if s is None:
        return None
    u = s.lower()
    if u in {"yes", "y", "true", "1"}:
        return True
    if u in {"no", "n", "false", "0"}:
        return False
    return None


def stable_restaurant_id(dedupe_key: str) -> str:
    """Short stable id from a dedupe key (name|city|neighborhood)."""
    h = hashlib.sha256(dedupe_key.encode("utf-8")).hexdigest()
    return h[:16]
