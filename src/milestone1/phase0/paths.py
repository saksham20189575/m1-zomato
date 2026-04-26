from __future__ import annotations

from pathlib import Path


def repo_root() -> Path:
    """Directory containing `pyproject.toml`, for `.env` and docs paths."""
    here = Path(__file__).resolve().parent
    for d in (here, *here.parents):
        if (d / "pyproject.toml").is_file():
            return d
    return Path.cwd()
