from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from milestone1.phase0.commands import bootstrap_env
from milestone1.phase2_preferences import (
    PreferencesValidationError,
    parse_cuisine_list,
    preferences_from_mapping,
)


def cmd_prefs_parse(args: argparse.Namespace) -> int:
    """Validate CLI-style preference flags (Phase 2)."""
    bootstrap_env()
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

    try:
        prefs = preferences_from_mapping(payload, allowed_city_names=allowed)
    except PreferencesValidationError as e:
        print("Validation failed:", file=sys.stderr)
        for field, msg in e.errors:
            print(f"  {field}: {msg}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    out = {
        "location": prefs.location,
        "budget_band": prefs.budget_band.value if prefs.budget_band else None,
        "cuisines": list(prefs.cuisines),
        "minimum_rating": prefs.minimum_rating,
        "additional_preferences": prefs.additional_preferences,
    }
    print(json.dumps(out, indent=2))
    return 0


def register(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    pp = subparsers.add_parser("prefs-parse", help="Phase 2: validate preferences and print JSON.")
    pp.add_argument("--location", required=True)
    pp.add_argument("--budget", default=None, help="low | medium | high, or omit for any")
    pp.add_argument("--cuisine", action="append", default=None, metavar="NAME", help="Repeat for multiple cuisines")
    pp.add_argument("--cuisines", default=None, help="Comma-separated cuisines (alternative to --cuisine)")
    pp.add_argument("--min-rating", dest="min_rating", default=None)
    pp.add_argument("--additional", default=None)
    pp.add_argument(
        "--allowed-cities-file",
        default=None,
        help="Optional file: one allowed city per line (case-insensitive match)",
    )


def dispatch(command: str, args: argparse.Namespace) -> int | None:
    if command == "prefs-parse":
        return cmd_prefs_parse(args)
    return None
