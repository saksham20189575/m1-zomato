from __future__ import annotations

import argparse
import json
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
from milestone1.phase3_integration.build import build_integration_output


def cmd_prompt_build(args: argparse.Namespace) -> int:
    """Load restaurants, validate prefs, print integration JSON (Phase 3)."""
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

    out = build_integration_output(rows, prefs, candidate_cap=cap)
    doc: dict[str, object] = {
        "matched_count": out.matched_count,
        "candidate_count": len(out.candidates),
        "candidate_ids": [r.id for r in out.candidates],
    }
    if args.omit_prompt_text:
        doc["prompt"] = {
            "system_message_len": len(out.prompt.system_message),
            "user_message_len": len(out.prompt.user_message),
        }
    else:
        doc["prompt"] = {
            "system_message": out.prompt.system_message,
            "user_message": out.prompt.user_message,
        }

    print(json.dumps(doc, indent=2))
    return 0


def register(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    pb = subparsers.add_parser(
        "prompt-build",
        help="Phase 3: filter restaurants, cap candidates, print prompt payload (no LLM).",
    )
    pb.add_argument("--location", required=True)
    pb.add_argument("--budget", default=None, help="low | medium | high, or omit for any")
    pb.add_argument("--cuisine", action="append", default=None, metavar="NAME")
    pb.add_argument("--cuisines", default=None, help="Comma-separated cuisines")
    pb.add_argument("--min-rating", dest="min_rating", default=None)
    pb.add_argument("--additional", default=None)
    pb.add_argument(
        "--allowed-cities-file",
        default=None,
        help="Optional file: one city per line; default is cities from loaded rows",
    )
    pb.add_argument(
        "--load-limit",
        type=int,
        default=None,
        metavar="N",
        help="Load at most N restaurants from the Hub (default: full stream scan)",
    )
    pb.add_argument(
        "--cap",
        type=int,
        default=DEFAULT_CANDIDATE_CAP,
        help=f"Max candidates after filters (default: {DEFAULT_CANDIDATE_CAP})",
    )
    pb.add_argument(
        "--omit-prompt-text",
        action="store_true",
        help="Print prompt lengths only (smaller JSON for quick checks)",
    )


def dispatch(command: str, args: argparse.Namespace) -> int | None:
    if command == "prompt-build":
        return cmd_prompt_build(args)
    return None
