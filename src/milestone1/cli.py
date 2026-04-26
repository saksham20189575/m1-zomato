from __future__ import annotations

import argparse
import sys

from milestone1.phase0 import commands as phase0_cmds
from milestone1.phase1_ingestion import commands as phase1_cmds
from milestone1.phase2_preferences import commands as phase2_cmds
from milestone1.phase3_integration import commands as phase3_cmds
from milestone1.phase4_llm import commands as phase4_cmds
from milestone1.phase5_output import commands as phase5_cmds

_PHASE_MODULES = (phase0_cmds, phase1_cmds, phase2_cmds, phase3_cmds, phase4_cmds, phase5_cmds)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="milestone1", description="Restaurant recommendation milestone 1.")
    sub = p.add_subparsers(dest="command", required=True)
    for mod in _PHASE_MODULES:
        mod.register(sub)
    return p


def main(argv: list[str] | None = None) -> None:
    argv = argv if argv is not None else sys.argv[1:]
    parser = build_parser()
    args = parser.parse_args(argv)
    for mod in _PHASE_MODULES:
        rc = mod.dispatch(args.command, args)
        if rc is not None:
            raise SystemExit(rc)
    parser.error(f"unknown command {args.command!r}")
