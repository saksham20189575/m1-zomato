# Milestone 1 — AI restaurant recommendations

Zomato-style recommendations using structured data plus an LLM. See `docs/problemstatement.md` for the full brief and `docs/phased-architecture.md` for phases.

## Phase-wise layout

Source and tests are organized **by phase** so each milestone lives in its own folder.

```
src/milestone1/
  cli.py                 # composes per-phase command modules
  __main__.py
  phase0/                # scope, paths, info/doctor
  phase1_ingestion/      # Restaurant model, HF load, normalize, dedupe
  phase2_preferences/    # UserPreferences, validation
  phase3_integration/    # filters + prompt assembly
  phase4_llm/            # Groq client + recommend_with_groq
  phase5_output/         # markdown/plain render + telemetry helpers
  phase6_api/            # FastAPI HTTP API (Phase 6)
  phase8_streamlit/      # Streamlit UI + deploy path (Phase 8, optional extra)
tests/
  phase0/ …
frontend/                # Vite + React web UI (Phase 7) — see “Run the web app”
streamlit_app.py         # Phase 8 entry for `streamlit run` / Streamlit Cloud
```

Each `phaseN_*` package through Phase 5 may own a `commands.py` registered from `cli.py`. **Phase 6 (API) and Phase 7 (web)** are started separately from the `milestone1` CLI. **Phase 8 (Streamlit)** is optional; see below.

## Setup

```bash
cd /path/to/milestone1
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
# optional: Streamlit Phase 8 UI
# pip install -e ".[streamlit]"
cp .env.example .env        # add keys when you reach Phase 4+
```

## Phase 0 — Foundations

```bash
milestone1 info       # scope + secret hints
milestone1 doctor     # same + Python version gate
```

Docs: `docs/phase0-scope.md`.

## Phase 1 — Ingestion (`src/milestone1/phase1_ingestion/`)

Canonical `Restaurant` model, Hugging Face streaming load, pinned dataset revision, dedupe by name+city+neighborhood.

```bash
milestone1 ingest-smoke --limit 5
```

Optional Hub integration test:

```bash
RUN_HF_INTEGRATION=1 pytest -m integration
```

Docs: `docs/dataset-contract.md`.

## Phase 2 — Preferences (`src/milestone1/phase2_preferences/`)

Normalized `UserPreferences`, `PreferencesValidationError` with per-field messages, and `preferences_from_mapping()` for web-style dict payloads.

```bash
milestone1 prefs-parse --location Bangalore --budget medium --cuisine Italian --min-rating 3.5
```

Optional corpus check (one city per line):

```bash
milestone1 prefs-parse --location bangalore --allowed-cities-file path/to/cities.txt
```

## Phase 6 — HTTP API (`src/milestone1/phase6_api/`)

FastAPI service: **`POST /api/v1/recommendations`** (preferences JSON + optional `load_limit` / `candidate_cap` / `top_k` / Groq tuning), **`GET /health`** (includes `groq_configured`), **`GET /api/v1/meta`** (`cities` sample for form hints). **`GROQ_API_KEY`** stays on the server only. Interactive docs: **`http://127.0.0.1:8000/docs`** after start.

```bash
milestone1-api
# or: uvicorn milestone1.phase6_api.app:app --host 127.0.0.1 --port 8000
```

Optional **`CORS_ORIGINS`** (comma-separated); defaults include `http://localhost:5173` and `http://localhost:3000` for local frontends.

**Phase 7 UI + design tools:** a ready-to-paste **Google Stitch** prompt (Next.js-oriented; the repo UI is Vite) is in [`docs/frontend-stitch-prompt.md`](docs/frontend-stitch-prompt.md).

## Phase 7 — Web UI (`frontend/`)

**Vite 5** + **React 18** + TypeScript + Tailwind. The browser only calls the Phase 6 API; set **`VITE_API_BASE_URL`** if the API is not on `http://127.0.0.1:8000` (see `frontend/.env.local.example`).

**Run API + web UI together** (one command from `frontend/`; Node 20+ recommended):

```bash
cd frontend
cp .env.local.example .env.local   # adjust if needed
npm install
npm run dev:all
```

`dev:all` starts **`milestone1-api`** (activate venv in the parent project) and **Vite** on `http://localhost:5173`. Put **`GROQ_API_KEY`** in the project root `.env` for live LLM calls.

**Run separately** (optional):

```bash
# API
source .venv/bin/activate
milestone1-api
```

```bash
# UI only
cd frontend
npm run dev
```

Open **http://localhost:5173** — the UI includes location hints from **`GET /api/v1/meta`**, form fields matching Phase 2, two distinct empty states, result cards, optional Groq “advanced” fields, and **Copy as Markdown**.

## Phase 8 — Streamlit (`streamlit_app.py`)

All-Python UI that calls the **same** recommendation path as the HTTP API (`recommend_to_response`), without Node or a separate API process. Useful for demos and [Streamlit Community Cloud](https://streamlit.io/cloud).

```bash
pip install -e ".[streamlit]"
# GROQ_API_KEY in project root .env (same as Phase 6)
streamlit run streamlit_app.py
```

Deploy notes, Cloud secrets, and troubleshooting: [`docs/streamlit-deploy.md`](docs/streamlit-deploy.md). Optional requirements file for hosts that need it: [`requirements-streamlit.txt`](requirements-streamlit.txt).

## Tests

```bash
pytest                                    # all phase folders, no network
RUN_HF_INTEGRATION=1 pytest -m integration  # Phase 1 Hub smoke
```

## Secrets

Never commit `.env`. Supported variables are listed in `.env.example`.
