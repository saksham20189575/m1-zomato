from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from datasets import IterableDataset, load_dataset

from milestone1.phase1_ingestion.constants import (
    DATASET_NAME,
    DATASET_REVISION,
    REQUIRED_HF_COLUMNS,
    SPLIT,
)
from milestone1.phase1_ingestion.convert import row_to_restaurant
from milestone1.phase1_ingestion.errors import IngestionError
from milestone1.phase1_ingestion.model import Restaurant


def assert_hub_row_schema(row: dict[str, Any]) -> None:
    keys = set(row.keys())
    missing = REQUIRED_HF_COLUMNS - keys
    if missing:
        raise IngestionError(
            "Hub row missing required columns (dataset schema may have changed): "
            + ", ".join(sorted(missing))
        )


def _iter_hf_rows(*, revision: str | None = DATASET_REVISION) -> Iterator[dict[str, Any]]:
    ds = load_dataset(
        DATASET_NAME,
        split=SPLIT,
        revision=revision,
        streaming=True,
        trust_remote_code=False,
    )
    if not isinstance(ds, IterableDataset):
        raise IngestionError("Expected streaming IterableDataset from load_dataset")
    first = True
    for row in ds:
        r = dict(row)
        if first:
            assert_hub_row_schema(r)
            first = False
        yield r


def iter_restaurants(
    *,
    limit: int | None = None,
    dedupe: bool = True,
    revision: str | None = DATASET_REVISION,
) -> Iterator[Restaurant]:
    """
    Stream normalized restaurants from the Hub.

    ``dedupe`` uses ``(name, city, neighborhood)``; first occurrence wins.
    """
    seen: set[str] = set()
    n = 0
    for row in _iter_hf_rows(revision=revision):
        rec = row_to_restaurant(row)
        if rec is None:
            continue
        if dedupe:
            key = rec.id
            if key in seen:
                continue
            seen.add(key)
        yield rec
        n += 1
        if limit is not None and n >= limit:
            break


def load_restaurants(
    *,
    limit: int | None = None,
    dedupe: bool = True,
    revision: str | None = DATASET_REVISION,
) -> list[Restaurant]:
    """
    Load restaurants into memory.

    Warning: ``limit=None`` pulls the full split (~51k rows) — fine for batch jobs,
    expensive for interactive use. Prefer ``iter_restaurants`` or a positive ``limit``.
    """
    return list(iter_restaurants(limit=limit, dedupe=dedupe, revision=revision))
