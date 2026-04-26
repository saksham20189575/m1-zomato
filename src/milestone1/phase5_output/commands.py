from __future__ import annotations

import argparse
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
from milestone1.phase4_llm.recommend import recommend_with_groq
from milestone1.phase5_output.observability import emit_recommendation_telemetry
from milestone1.phase5_output.render import render_report_markdown, render_report_plain


def cmd_recommend_run(args: argparse.Namespace) -> int:
    """Demo path: prefs → Groq (Phase 4) → readable report + telemetry (Phase 5)."""
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

    if not args.no_telemetry:
        emit_recommendation_telemetry(result)

    fmt = str(args.format).lower()
    if fmt == "plain":
        print(render_report_plain(result), end="")
    elif fmt == "markdown":
        print(render_report_markdown(result), end="")
    else:
        print(f"ERROR: unknown --format {args.format!r}", file=sys.stderr)
        return 1
    return 0


def register(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    rr = subparsers.add_parser(
        "recommend-run",
        help="Phase 5: human-readable recommendations + stderr telemetry JSON line.",
    )
    rr.add_argument("--location", required=True)
    rr.add_argument("--budget", default=None)
    rr.add_argument("--cuisine", action="append", default=None, metavar="NAME")
    rr.add_argument("--cuisines", default=None)
    rr.add_argument("--min-rating", dest="min_rating", default=None)
    rr.add_argument("--additional", default=None)
    rr.add_argument("--allowed-cities-file", default=None)
    rr.add_argument("--load-limit", type=int, default=None, metavar="N")
    rr.add_argument("--cap", type=int, default=DEFAULT_CANDIDATE_CAP)
    rr.add_argument("--top-k", type=int, default=DEFAULT_TOP_K)
    rr.add_argument(
        "--model",
        default=None,
        help=f"Groq model id (default: env GROQ_MODEL or {DEFAULT_GROQ_MODEL})",
    )
    rr.add_argument("--temperature", type=float, default=DEFAULT_TEMPERATURE)
    rr.add_argument("--max-tokens", type=int, default=DEFAULT_MAX_TOKENS)
    rr.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT_SEC)
    rr.add_argument(
        "--format",
        choices=("markdown", "plain"),
        default="markdown",
        help="Output format for stdout (default: markdown)",
    )
    rr.add_argument(
        "--no-telemetry",
        action="store_true",
        help="Do not print the JSON telemetry line to stderr",
    )


def dispatch(command: str, args: argparse.Namespace) -> int | None:
    if command == "recommend-run":
        return cmd_recommend_run(args)
    return None
