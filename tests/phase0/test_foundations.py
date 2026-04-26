import sys
from pathlib import Path

from milestone1.phase0.paths import repo_root
from milestone1.phase0.scope import PYTHON_MIN


def test_repo_root_contains_pyproject() -> None:
    root = repo_root()
    assert (root / "pyproject.toml").is_file()


def test_repo_root_stable_from_package() -> None:
    assert repo_root() == Path(__file__).resolve().parents[2]


def test_python_version_minimum_documented() -> None:
    assert sys.version_info >= PYTHON_MIN
