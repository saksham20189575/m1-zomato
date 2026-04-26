import os

import pytest

pytestmark = pytest.mark.integration


@pytest.mark.skipif(
    not os.environ.get("RUN_HF_INTEGRATION"),
    reason="Set RUN_HF_INTEGRATION=1 to run Hub download tests.",
)
def test_load_restaurants_small_limit() -> None:
    from milestone1.phase1_ingestion import load_restaurants

    rows = load_restaurants(limit=5, dedupe=True)
    assert len(rows) == 5
    assert all(r.name for r in rows)
    assert all(r.id for r in rows)
