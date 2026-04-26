from __future__ import annotations

import argparse
import sys

from milestone1.phase0.commands import bootstrap_env


def cmd_ingest_smoke(limit: int) -> int:
    """Load a handful of restaurants to verify Phase 1 ingestion."""
    bootstrap_env()
    if limit < 1:
        print("ERROR: --limit must be >= 1", file=sys.stderr)
        return 1
    try:
        from milestone1.phase1_ingestion import load_restaurants
    except ImportError as e:
        print(f"ERROR: ingestion package not available: {e}", file=sys.stderr)
        return 1
    try:
        rows = load_restaurants(limit=limit, dedupe=True)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    print(f"Loaded {len(rows)} restaurant(s) (limit={limit})")
    for r in rows[: min(3, len(rows))]:
        print(f"  - {r.name} | {r.city} | {r.budget_band.value} | rating={r.rating}")
    return 0


def register(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    smoke = subparsers.add_parser(
        "ingest-smoke",
        help="Phase 1: load N restaurants from Hugging Face (network).",
    )
    smoke.add_argument("--limit", type=int, default=5, help="Number of restaurants after dedupe (default: 5).")


def dispatch(command: str, args: argparse.Namespace) -> int | None:
    if command == "ingest-smoke":
        return cmd_ingest_smoke(getattr(args, "limit", 5))
    return None
