from __future__ import annotations

import logging
import os
import threading

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.requests import Request

from milestone1.phase0.paths import repo_root
from milestone1.phase2_preferences import PreferencesValidationError
from milestone1.phase6_api.constants import (
    DEFAULT_CORS_ORIGINS,
    DEFAULT_LOAD_LIMIT,
    DEFAULT_META_CITIES_CAP,
    ENV_CORS_ORIGINS,
    MAX_LOAD_LIMIT,
    MIN_LOAD_LIMIT,
    MAX_META_CITIES_CAP,
    MIN_META_CITIES_CAP,
)
from milestone1.phase6_api.schemas import HealthResponse, MetaResponse, RecommendRequest, RecommendResponse
from milestone1.phase6_api.service import (
    groq_configured,
    meta_cities,
    prewarm_locations,
    recommend_to_response,
)

_log = logging.getLogger("milestone1.phase6_api")


def _cors_origins() -> list[str]:
    raw = os.environ.get(ENV_CORS_ORIGINS, "").strip()
    if not raw:
        return list(DEFAULT_CORS_ORIGINS)
    return [o.strip() for o in raw.split(",") if o.strip()]


def create_app() -> FastAPI:
    from dotenv import load_dotenv

    load_dotenv(repo_root() / ".env")

    app = FastAPI(
        title="Milestone1 Restaurant API",
        version="0.1.0",
        description="Phase 6 HTTP API over Phases 1–5 (recommendations via Groq + HF dataset).",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=_cors_origins(),
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )

    @app.exception_handler(PreferencesValidationError)
    async def _prefs_validation(_request: Request, exc: PreferencesValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={"detail": {"errors": [{"field": f, "message": m} for f, m in exc.errors]}},
        )

    @app.on_event("startup")
    def _prewarm() -> None:
        def _run() -> None:
            try:
                _log.info("prewarm: loading locations from HF Hub…")
                n = prewarm_locations(DEFAULT_LOAD_LIMIT)
                _log.info("prewarm: cached %d locations", n)
            except Exception as exc:
                _log.warning("prewarm: failed (%s); first /meta call will load on demand", exc)

        threading.Thread(target=_run, name="prewarm-locations", daemon=True).start()

    @app.get("/health", response_model=HealthResponse, tags=["ops"])
    def health() -> HealthResponse:
        return HealthResponse(status="ok", groq_configured=groq_configured())

    @app.post("/api/v1/recommendations", response_model=RecommendResponse, tags=["recommendations"])
    def post_recommendations(body: RecommendRequest) -> RecommendResponse:
        return recommend_to_response(body)

    @app.get("/api/v1/meta", response_model=MetaResponse, tags=["meta"])
    def get_meta(
        load_limit: int = Query(default=DEFAULT_LOAD_LIMIT, ge=MIN_LOAD_LIMIT, le=MAX_LOAD_LIMIT),
        cities_cap: int = Query(
            default=DEFAULT_META_CITIES_CAP,
            ge=MIN_META_CITIES_CAP,
            le=MAX_META_CITIES_CAP,
        ),
    ) -> MetaResponse:
        return meta_cities(load_limit=load_limit, cities_cap=cities_cap)

    return app


app = create_app()
