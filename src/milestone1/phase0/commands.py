from __future__ import annotations

import argparse
import os
import sys

from dotenv import load_dotenv

from milestone1 import __version__
from milestone1.phase0.paths import repo_root
from milestone1.phase0.scope import (
    DATASET_ID,
    DATASET_SPLIT,
    DEV_CLI,
    PREFERENCE_FIELDS_V1,
    PYTHON_MIN,
    USER_INPUT_SURFACE,
)


def bootstrap_env() -> None:
    load_dotenv(repo_root() / ".env")


def cmd_info() -> int:
    """Print Phase 0 assumptions and environment readiness."""
    bootstrap_env()
    print(f"milestone1 {__version__} — Phase 0 foundations")
    print()
    print("Product")
    print(f"  User input & results: {USER_INPUT_SURFACE} (basic web UI — source of input)")
    print(f"  Developer / diagnostics: {DEV_CLI} (this CLI)")
    print(f"  Dataset: {DATASET_ID} (split={DATASET_SPLIT})")
    print()
    print("Preferences (v1 intent)")
    for f in PREFERENCE_FIELDS_V1:
        print(f"  - {f}")
    print()
    groq = bool(os.environ.get("GROQ_API_KEY", "").strip())
    openai_style = os.environ.get("OPENAI_API_KEY") or os.environ.get("LLM_API_KEY")
    print("Secrets")
    if groq:
        print("  GROQ_API_KEY: set (Phase 4 Groq recommend)")
    else:
        print("  GROQ_API_KEY: not set (required for `milestone1 recommend`; see .env.example)")
    if openai_style:
        print("  OPENAI_API_KEY / LLM_API_KEY: set (optional legacy names)")
    else:
        print("  OPENAI_API_KEY / LLM_API_KEY: not set (optional)")
    if os.environ.get("HF_TOKEN"):
        print("  HF_TOKEN: set (optional; improves Hub rate limits)")
    else:
        print("  HF_TOKEN: not set (optional)")
    return 0


def cmd_doctor() -> int:
    """``info`` plus a Python version gate."""
    code = cmd_info()
    if sys.version_info < PYTHON_MIN:
        print()
        print(f"ERROR: Python {PYTHON_MIN[0]}.{PYTHON_MIN[1]}+ required.", file=sys.stderr)
        return 1
    return code


def register(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    subparsers.add_parser("info", help="Show Phase 0 scope and environment summary.")
    subparsers.add_parser("doctor", help="Like info, but fail if Python version is below minimum.")


def dispatch(command: str, args: argparse.Namespace) -> int | None:
    if command == "info":
        return cmd_info()
    if command == "doctor":
        return cmd_doctor()
    return None
