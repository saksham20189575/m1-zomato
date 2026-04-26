from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from milestone1.phase0.commands import bootstrap_env
from milestone1.phase1_ingestion import load_restaurants
from milestone1.phase2_preferences import (
    PreferencesValidationError,
    allowed_cities_from_restaurants,
    parse_cuisine_list,
    preferences_from_mapping,
)
from milestone1.phase3_integration.constants import (
    DEFAULT_CANDIDATE_CAP,
    MAX_CANDIDATE_CAP,
    MIN_CANDIDATE_CAP,
)
from milestone1.phase4_llm.constants import (
    DEFAULT_GROQ_MODEL,
    DEFAULT_MAX_TOKENS,
    DEFAULT_TEMPERATURE,
    DEFAULT_TIMEOUT_SEC,
    DEFAULT_TOP_K,
)
from milestone1.phase4_llm.model import RankedRecommendation
from milestone1.phase4_llm.recommend import recommend_with_groq


def _restaurant_snapshot(r: RankedRecommendation) -> dict[str, object] | None:
    if r.restaurant is None:
        return None
    x = r.restaurant
    return {
        "id": x.id,
        "name": x.name,
        "city": x.city,
        "cuisines": list(x.cuisines),
        "rating": x.rating,
        "approx_cost_two_inr": x.approx_cost_two,
        "budget_band": x.budget_band.value,
    }


def cmd_recommend(args: argparse.Namespace) -> int:
    """End-to-end: load data, integrate, call Groq, print JSON rankings."""
    bootstrap_env()
    cap = int(args.cap)
    if cap < MIN_CANDIDATE_CAP or cap > MAX_CANDIDATE_CAP:
        print(
            f"ERROR: --cap must be between {MIN_CANDIDATE_CAP} and {MAX_CANDIDATE_CAP}.",
            file=sys.stderr,
        )
        return 1

    load_limit = args.load_limit
    if load_limit is not None and load_limit < 1:
        print("ERROR: --load-limit must be >= 1 when set.", file=sys.stderr)
        return 1

    try:
        rows = load_restaurants(limit=load_limit, dedupe=True)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    cuisines: list[str] = list(args.cuisine or [])
    if args.cuisines:
        cuisines.extend(parse_cuisine_list(args.cuisines))
    payload: dict[str, object] = {
        "location": args.location,
        "budget": args.budget,
        "minimum_rating": args.min_rating,
        "additional_preferences": args.additional,
    }
    if cuisines:
        payload["cuisines"] = cuisines

    allowed: list[str] | None = None
    if args.allowed_cities_file:
        p = Path(args.allowed_cities_file)
        if not p.is_file():
            print(f"ERROR: file not found: {p}", file=sys.stderr)
            return 1
        allowed = [ln.strip() for ln in p.read_text(encoding="utf-8").splitlines() if ln.strip()]
    else:
        allowed = sorted(allowed_cities_from_restaurants(rows))

    try:
        prefs = preferences_from_mapping(payload, allowed_city_names=allowed)
    except PreferencesValidationError as e:
        print("Validation failed:", file=sys.stderr)
        for field, msg in e.errors:
            print(f"  {field}: {msg}", file=sys.stderr)
        return 1

    result = recommend_with_groq(
        rows,
        prefs,
        candidate_cap=cap,
        top_k=int(args.top_k),
        model=args.model,
        temperature=float(args.temperature),
        max_tokens=int(args.max_tokens),
        timeout_sec=float(args.timeout),
    )

    resolved_model = args.model or os.environ.get("GROQ_MODEL", DEFAULT_GROQ_MODEL)
    doc: dict[str, object] = {
        "source": result.source,
        "matched_count": result.matched_count,
        "candidate_count": result.candidate_count,
        "latency_ms": result.latency_ms,
        "usage": result.usage,
        "detail": result.detail,
        "model": resolved_model,
        "rankings": [
            {
                "rank": r.rank,
                "restaurant_id": r.restaurant_id,
                "explanation": r.explanation,
                "restaurant": _restaurant_snapshot(r),
            }
            for r in result.rankings
        ],
    }
    print(json.dumps(doc, indent=2))
    return 0


def register(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    rc = subparsers.add_parser(
        "recommend",
        help="Phase 4: Groq LLM rankings (JSON) with deterministic fallback.",
    )
    rc.add_argument("--location", required=True)
    rc.add_argument("--budget", default=None)
    rc.add_argument("--cuisine", action="append", default=None, metavar="NAME")
    rc.add_argument("--cuisines", default=None)
    rc.add_argument("--min-rating", dest="min_rating", default=None)
    rc.add_argument("--additional", default=None)
    rc.add_argument("--allowed-cities-file", default=None)
    rc.add_argument("--load-limit", type=int, default=None, metavar="N")
    rc.add_argument("--cap", type=int, default=DEFAULT_CANDIDATE_CAP)
    rc.add_argument(
        "--top-k",
        type=int,
        default=DEFAULT_TOP_K,
        help=f"Max rankings to return after parse (default: {DEFAULT_TOP_K})",
    )
    rc.add_argument(
        "--model",
        default=None,
        help=f"Groq model id (default: env GROQ_MODEL or {DEFAULT_GROQ_MODEL})",
    )
    rc.add_argument("--temperature", type=float, default=DEFAULT_TEMPERATURE)
    rc.add_argument("--max-tokens", type=int, default=DEFAULT_MAX_TOKENS)
    rc.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT_SEC, help="HTTP timeout seconds")


def dispatch(command: str, args: argparse.Namespace) -> int | None:
    if command == "recommend":
        return cmd_recommend(args)
    return None
