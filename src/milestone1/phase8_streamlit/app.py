"""Streamlit Phase 8 app: preferences → same stack as Phase 6 API (library in-process)."""

from __future__ import annotations

import html
import json
import os
from typing import Any

import streamlit as st
from dotenv import load_dotenv
from pydantic import ValidationError

from milestone1.phase0.paths import repo_root
from milestone1.phase2_preferences import PreferencesValidationError
from milestone1.phase4_llm.model import RankedRecommendation, RecommendResult
from milestone1.phase5_output.empty_copy import (
    EmptyPresentationKind,
    empty_state_body,
    empty_state_headline,
    presentation_kind,
)
from milestone1.phase6_api.constants import DEFAULT_LOAD_LIMIT, DEFAULT_META_CITIES_CAP
from milestone1.phase6_api.schemas import RecommendRequest, RecommendResponse
from milestone1.phase6_api.service import groq_configured, meta_cities, recommend_to_response

_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Playfair+Display:wght@700&display=swap');

html, body, [data-testid="stAppViewContainer"] *:not(code):not(pre) {
    font-family: 'Inter', system-ui, -apple-system, "Segoe UI", Roboto, sans-serif !important;
}
[data-testid="stHeader"] { background: transparent; }
[data-testid="stAppViewContainer"] { background: #fafafa; }

.m1-hero {
    background: linear-gradient(135deg, #ef4f5e 0%, #c43c4c 100%);
    color: #ffffff;
    padding: 2rem 1.75rem;
    border-radius: 18px;
    margin: 0.25rem 0 1.5rem;
    box-shadow: 0 16px 40px rgba(239, 79, 94, 0.22);
}
.m1-hero h1 {
    font-family: 'Playfair Display', Georgia, serif !important;
    font-weight: 700;
    font-size: 2.25rem;
    line-height: 1.1;
    margin: 0 0 0.4rem 0;
    color: #ffffff;
}
.m1-hero p { margin: 0; opacity: 0.92; font-size: 0.95rem; }

div[data-testid="stForm"] {
    background: #ffffff;
    border: 1px solid rgba(15, 23, 42, 0.06);
    border-radius: 16px;
    padding: 1.1rem 1.25rem 0.5rem;
    box-shadow: 0 2px 10px rgba(15, 23, 42, 0.04);
}

div[data-testid="stForm"] button[kind="primaryFormSubmit"],
div.stButton > button[kind="primary"] {
    background: #ef4f5e;
    border-color: #ef4f5e;
    font-weight: 600;
    border-radius: 10px;
}
div[data-testid="stForm"] button[kind="primaryFormSubmit"]:hover,
div.stButton > button[kind="primary"]:hover {
    background: #d63d4c;
    border-color: #d63d4c;
}

.m1-card {
    background: #ffffff;
    border: 1px solid rgba(15, 23, 42, 0.06);
    border-radius: 16px;
    padding: 1.1rem 1.25rem 1rem;
    margin: 0.65rem 0;
    box-shadow: 0 2px 10px rgba(15, 23, 42, 0.04);
}
.m1-card-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    margin-bottom: 0.5rem;
}
.m1-card-title { display: flex; align-items: baseline; gap: 8px; min-width: 0; }
.m1-card-title h3 {
    margin: 0;
    font-weight: 700;
    color: #111827;
    font-size: 1.05rem;
    overflow: hidden; text-overflow: ellipsis;
}
.m1-rank {
    background: #fef2f3;
    color: #ef4f5e;
    font-weight: 700;
    font-size: 0.72rem;
    padding: 2px 9px;
    border-radius: 999px;
    flex: none;
}
.m1-rating {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    background: #fff8e1;
    color: #b45309;
    font-weight: 600;
    padding: 3px 10px;
    border-radius: 999px;
    font-size: 0.82rem;
    flex: none;
}
.m1-rating--empty { color: #6b7280; background: #f3f4f6; }
.m1-reason {
    background: #fdf2f3;
    border-left: 3px solid #ef4f5e;
    padding: 0.7rem 0.95rem;
    border-radius: 8px;
    color: #1f2937;
    font-size: 0.93rem;
    line-height: 1.5;
    margin: 0.4rem 0 0.65rem;
}
.m1-meta { display: flex; flex-wrap: wrap; gap: 6px; }
.m1-chip {
    background: #f3f4f6;
    color: #374151;
    font-size: 0.78rem;
    padding: 3px 10px;
    border-radius: 999px;
}

.m1-status { color: #6b7280; font-size: 0.82rem; margin: 0.5rem 0 1rem; }
</style>
"""


def _bootstrap_env() -> None:
    """Local `.env` + Streamlit Cloud `st.secrets` → `os.environ` (Groq only)."""
    load_dotenv(repo_root() / ".env")
    try:
        sec: Any = st.secrets
        if "GROQ_API_KEY" in sec:
            os.environ["GROQ_API_KEY"] = str(sec["GROQ_API_KEY"]).strip()
        if "GROQ_MODEL" in sec:
            os.environ["GROQ_MODEL"] = str(sec["GROQ_MODEL"]).strip()
    except (RuntimeError, FileNotFoundError, KeyError):
        # Not running under Streamlit, or no secrets file — rely on `.env` / host env.
        pass


def _response_as_result(resp: RecommendResponse) -> RecommendResult:
    """Adapt API DTO to Phase 5 ``RecommendResult`` for shared empty-state helpers."""
    rankings = tuple(
        RankedRecommendation(
            restaurant_id=r.restaurant_id,
            rank=r.rank,
            explanation=r.explanation,
            restaurant=None,
        )
        for r in resp.rankings
    )
    return RecommendResult(
        source=resp.source,
        rankings=rankings,
        matched_count=resp.matched_count,
        candidate_count=resp.candidate_count,
        usage=resp.usage,
        latency_ms=resp.latency_ms,
        detail=resp.detail,
    )


@st.cache_data(ttl=600, show_spinner="Loading city list from dataset…")
def _cached_cities() -> tuple[list[str], bool]:
    m = meta_cities(load_limit=DEFAULT_LOAD_LIMIT, cities_cap=DEFAULT_META_CITIES_CAP)
    return m.cities, m.truncated


def _render_card(
    rank: int,
    name: str,
    rating: float | None,
    explanation: str,
    meta_bits: list[str],
) -> None:
    rating_html = (
        f'<span class="m1-rating">★ {rating:.1f}</span>'
        if rating is not None
        else '<span class="m1-rating m1-rating--empty">Not rated</span>'
    )
    chips = "".join(
        f'<span class="m1-chip">{html.escape(b)}</span>' for b in meta_bits if b
    )
    st.markdown(
        f"""
        <div class="m1-card">
          <div class="m1-card-head">
            <div class="m1-card-title">
              <span class="m1-rank">#{rank}</span>
              <h3>{html.escape(name)}</h3>
            </div>
            {rating_html}
          </div>
          <div class="m1-reason">{html.escape(explanation)}</div>
          <div class="m1-meta">{chips}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    _bootstrap_env()

    st.set_page_config(
        page_title="Milestone1 — Recommendations",
        page_icon="🍽️",
        layout="centered",
        initial_sidebar_state="collapsed",
    )
    st.markdown(_CSS, unsafe_allow_html=True)

    with st.sidebar:
        st.subheader("Status")
        st.write("Groq API key:", "✓ configured" if groq_configured() else "✗ missing")
        st.divider()
        st.markdown(
            "Set **`GROQ_API_KEY`** (and optional **`GROQ_MODEL`**) via "
            "[Streamlit secrets](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management) "
            "or a project root `.env` locally."
        )

    st.markdown(
        '<div class="m1-hero">'
        '<h1>Find your next great meal</h1>'
        '<p>AI-grounded recommendations from a curated Zomato dataset.</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    try:
        cities, truncated = _cached_cities()
    except Exception as exc:
        st.error(f"Could not load dataset metadata: {exc}")
        st.stop()

    if not cities:
        st.error("No cities returned from the dataset. Try again later.")
        st.stop()

    if truncated:
        st.caption("City list is truncated for performance; pick a location from the sample.")

    with st.form("prefs", clear_on_submit=False):
        location = st.selectbox(
            "Location",
            options=[""] + cities,
            format_func=lambda x: "— Select a city —" if x == "" else x,
        )
        col_a, col_b = st.columns(2)
        with col_a:
            cuisines_raw = st.text_input(
                "Cuisines",
                placeholder="e.g. North Indian, Chinese",
                help="Comma-separated.",
            )
        with col_b:
            budget = st.selectbox(
                "Budget",
                options=["", "low", "medium", "high"],
                format_func=lambda b: "Any" if b == "" else b.title(),
            )
        min_rating = st.select_slider(
            "Minimum rating",
            options=["Any", "3", "3.5", "4", "4.5", "5"],
            value="Any",
        )
        additional = st.text_area(
            "Additional preferences",
            height=110,
            placeholder="Dietary needs, vibe, dishes to avoid…",
            help="Free-form notes for the model.",
        )
        submitted = st.form_submit_button("Get recommendations", type="primary")

    if not submitted:
        st.markdown(
            '<div class="m1-status">Choose a city and submit the form to get picks.</div>',
            unsafe_allow_html=True,
        )
        return

    if not location.strip():
        st.warning("Please select a location.")
        return

    parts = [p.strip() for p in cuisines_raw.replace("|", ",").split(",") if p.strip()]
    rating_value = None if min_rating == "Any" else float(min_rating)
    try:
        req = RecommendRequest(
            location=location.strip(),
            budget=budget or None,
            cuisines=parts or None,
            minimum_rating=rating_value,
            additional_preferences=additional.strip() or None,
        )
    except ValidationError as exc:
        st.error("Invalid form values:")
        st.code(json.dumps(exc.errors(), indent=2, default=str), language="json")
        return

    if not groq_configured():
        st.error("Set **GROQ_API_KEY** in `.env` or Streamlit secrets before requesting recommendations.")
        return

    with st.spinner("Filtering candidates and calling the model…"):
        try:
            resp = recommend_to_response(req)
        except PreferencesValidationError as exc:
            st.error("Preferences could not be validated:")
            for field, msg in exc.errors:
                st.write(f"- **{field}:** {msg}")
            return
        except Exception as exc:
            st.exception(exc)
            return

    result = _response_as_result(resp)
    kind = presentation_kind(result)

    st.subheader("Personalized picks")
    latency = f' · {resp.latency_ms:.0f} ms' if resp.latency_ms is not None else ''
    st.markdown(
        f'<div class="m1-status">'
        f'Source: <code>{html.escape(resp.source)}</code> · matched {resp.matched_count} · '
        f'candidates {resp.candidate_count} · model <code>{html.escape(resp.model)}</code>'
        f'{latency}'
        f'</div>',
        unsafe_allow_html=True,
    )

    if resp.source == "fallback" and resp.detail:
        st.warning(f"Automated fallback: {resp.detail}")

    if kind is not EmptyPresentationKind.RESULTS:
        h = empty_state_headline(kind)
        b = empty_state_body(kind)
        if h:
            st.error(h)
        if b:
            st.write(b)
        return

    for r in resp.rankings:
        d = r.restaurant
        title = d.name if d else r.restaurant_id
        rating = d.rating if d else None
        meta_bits: list[str] = []
        if d:
            if d.cuisines:
                meta_bits.append(", ".join(d.cuisines))
            if d.approx_cost_two_inr is not None:
                meta_bits.append(f"₹{d.approx_cost_two_inr:,} for two")
            if d.budget_band:
                meta_bits.append(d.budget_band.title())
            if d.city:
                meta_bits.append(d.city)
        _render_card(r.rank, title, rating, r.explanation, meta_bits)

    with st.expander("Raw JSON (debug)"):
        st.json(resp.model_dump())


if __name__ == "__main__":
    main()
