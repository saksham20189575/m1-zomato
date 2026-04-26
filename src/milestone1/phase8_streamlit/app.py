"""Streamlit Phase 8 app: preferences → same stack as Phase 6 API (library in-process)."""

from __future__ import annotations

import json
import os
from typing import Any

import streamlit as st
from dotenv import load_dotenv
from pydantic import ValidationError

from milestone1.phase0.paths import repo_root
from milestone1.phase2_preferences import PreferencesValidationError
from milestone1.phase4_llm.constants import DEFAULT_TEMPERATURE, DEFAULT_TIMEOUT_SEC
from milestone1.phase4_llm.model import RankedRecommendation, RecommendResult
from milestone1.phase5_output.empty_copy import (
    EmptyPresentationKind,
    empty_state_body,
    empty_state_headline,
    presentation_kind,
)
from milestone1.phase6_api.constants import (
    DEFAULT_LOAD_LIMIT,
    DEFAULT_META_CITIES_CAP,
    MAX_LOAD_LIMIT,
    MAX_META_CITIES_CAP,
    MIN_LOAD_LIMIT,
    MIN_META_CITIES_CAP,
)
from milestone1.phase6_api.schemas import RecommendRequest, RecommendResponse
from milestone1.phase6_api.service import groq_configured, meta_cities, recommend_to_response


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
def _cached_meta(load_limit: int, cities_cap: int) -> tuple[list[str], bool]:
    m = meta_cities(load_limit=load_limit, cities_cap=cities_cap)
    return m.cities, m.truncated


def main() -> None:
    _bootstrap_env()

    st.set_page_config(
        page_title="Milestone1 — Recommendations",
        page_icon="🍽️",
        layout="centered",
    )

    st.title("Restaurant recommendations")
    st.caption("Phase 8 — Streamlit · same pipeline as the Phase 6 API (in-process).")

    with st.sidebar:
        st.subheader("Status")
        st.write("Groq API key:", "✓ configured" if groq_configured() else "✗ missing")
        st.divider()
        st.markdown(
            "Secrets: set **`GROQ_API_KEY`** (and optional **`GROQ_MODEL`**) in "
            "[Streamlit Cloud](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management) "
            "or use a project root `.env` locally."
        )

    load_limit = st.slider(
        "Dataset rows to scan (`load_limit`)",
        min_value=MIN_LOAD_LIMIT,
        max_value=min(MAX_LOAD_LIMIT, 20_000),
        value=min(DEFAULT_LOAD_LIMIT, 8_000),
        step=500,
        help="Lower values speed up Hub load on free tiers.",
    )
    cities_cap = st.number_input(
        "Max cities in location list",
        min_value=MIN_META_CITIES_CAP,
        max_value=MAX_META_CITIES_CAP,
        value=DEFAULT_META_CITIES_CAP,
        step=50,
    )

    try:
        cities, truncated = _cached_meta(int(load_limit), int(cities_cap))
    except Exception as exc:
        st.error(f"Could not load dataset metadata: {exc}")
        st.stop()

    if not cities:
        st.error("No cities returned for this load limit. Try raising **Dataset rows to scan**.")
        st.stop()

    if truncated:
        st.info("City list is truncated for performance; pick a location from the sample.")

    with st.form("prefs", clear_on_submit=False):
        location = st.selectbox(
            "Location",
            options=[""] + cities,
            format_func=lambda x: "— Select —" if x == "" else x,
        )
        cuisines_raw = st.text_input("Cuisines (comma-separated)", placeholder="e.g. North Indian, Chinese")
        budget = st.selectbox("Budget band", options=["", "low", "medium", "high"], format_func=lambda b: "Any" if b == "" else b.title())
        min_rating = st.selectbox(
            "Minimum rating",
            options=["", "3", "3.5", "4", "4.5", "5"],
            format_func=lambda x: "Any" if x == "" else f"{x}+ stars",
        )
        additional = st.text_area(
            "Additional preferences",
            height=100,
            placeholder="Dietary needs, vibe, dishes to avoid…",
            help=f"Combined with other notes; server max applies (see API docs).",
        )
        with st.expander("Advanced (model tuning)"):
            candidate_cap = st.number_input("candidate_cap", 1, 200, 30)
            top_k = st.number_input("top_k", 1, 50, 5)
            model = st.text_input("model (optional)", placeholder="Leave blank for default")
            temperature = st.number_input("temperature", 0.0, 2.0, float(DEFAULT_TEMPERATURE), 0.05)
            max_tokens = st.number_input("max_tokens", 64, 8192, 1024, 64)
            timeout = st.number_input("timeout (seconds)", 5.0, 300.0, float(DEFAULT_TIMEOUT_SEC), 5.0)

        submitted = st.form_submit_button("Get recommendations", type="primary")

    if not submitted:
        st.info("Choose a location and submit the form to run recommendations.")
        return

    if not location.strip():
        st.warning("Location is required.")
        return

    parts = [p.strip() for p in cuisines_raw.replace("|", ",").split(",") if p.strip()]
    try:
        req = RecommendRequest(
            location=location.strip(),
            budget=budget or None,
            cuisines=parts or None,
            minimum_rating=float(min_rating) if min_rating else None,
            additional_preferences=additional.strip() or None,
            load_limit=int(load_limit),
            candidate_cap=int(candidate_cap),
            top_k=int(top_k),
            model=model.strip() or None,
            temperature=float(temperature),
            max_tokens=int(max_tokens),
            timeout=float(timeout),
        )
    except ValidationError as exc:
        st.error("Invalid form values:")
        st.code(json.dumps(exc.errors(), indent=2), language="json")
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

    st.subheader("Results")
    st.caption(
        f"Source: `{resp.source}` · matched: {resp.matched_count} · candidates: {resp.candidate_count} · "
        f"model: `{resp.model}`"
        + (f" · {resp.latency_ms:.0f} ms" if resp.latency_ms is not None else "")
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
        with st.container():
            st.markdown(f"#### {r.rank}. {title}")
            col_a, col_b = st.columns([3, 1])
            with col_a:
                st.markdown(f"**Reason:** {r.explanation}")
            with col_b:
                if d and d.rating is not None:
                    st.metric("Rating", f"{d.rating:.1f}")
                else:
                    st.caption("Not rated")
            if d:
                bits = [
                    ", ".join(d.cuisines) if d.cuisines else None,
                    f"₹{d.approx_cost_two_inr:,} for two" if d.approx_cost_two_inr is not None else None,
                    d.budget_band,
                    d.city,
                ]
                st.caption(" · ".join(x for x in bits if x))
            st.divider()

    with st.expander("Raw JSON (debug)"):
        st.json(resp.model_dump())


if __name__ == "__main__":
    main()
