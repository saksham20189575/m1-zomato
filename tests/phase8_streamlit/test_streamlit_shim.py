from __future__ import annotations

import pytest

streamlit = pytest.importorskip("streamlit")


def test_main_is_callable() -> None:
    from milestone1.phase8_streamlit.app import main

    assert callable(main)
