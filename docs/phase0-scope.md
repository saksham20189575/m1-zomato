# Phase 0 — Scope and foundations (implemented)

This document satisfies **Phase 0** in [phased-architecture.md](./phased-architecture.md): product slice, stack, secrets, dataset contract pointer, non-goals, and how to run locally.

## Product slice (milestone 1)

| Decision | Choice |
|----------|--------|
| **Source of user input (and primary UX)** | **Basic web UI** — users enter preferences and view recommendations in the browser (built in later phases; Phase 0 locks this decision). |
| **CLI role** | **`milestone1`** / `python -m milestone1` — developer diagnostics and project health (`info`, `doctor`), not the primary way end users submit preferences. |
| **Rationale** | A small web UI matches the problem statement’s “clear, scannable results” and form-based preferences; the pipeline stays independent of the UI so the same core can be tested from code or CLI stubs if needed. |

## Stack

| Area | Choice |
|------|--------|
| Language | Python **3.11+** |
| Packaging | `pyproject.toml` + **setuptools**, installable in editable mode (`pip install -e .`) |
| Virtualenv | Project-local `.venv/` (gitignored) |
| Configuration / secrets | **python-dotenv** loads `.env` from the project root; **never commit** `.env`. See [`.env.example`](../.env.example). |
| Web (Phases 6–7) | **HTTP API (Phase 6)** + **basic web UI (Phase 7)** — see [phased-architecture.md](./phased-architecture.md); served locally for milestone 1; no production hosting requirement in Phase 0. |
| Data | **Hugging Face `datasets`** for [ManikaSaini/zomato-restaurant-recommendation](https://huggingface.co/datasets/ManikaSaini/zomato-restaurant-recommendation) (Phase 1+) |
| LLM (Phase 4+) | **`GROQ_API_KEY`** for Groq (OpenAI-compatible chat); see [`.env.example`](../.env.example). Legacy names `OPENAI_API_KEY` / `LLM_API_KEY` may appear in older docs only. |

## Supported preference fields (v1 intent)

Aligned with [problemstatement.md](./problemstatement.md). Exact validation arrives in Phase 2.

- **Location** — city/area string matching dataset geography.
- **Budget** — discrete band: low / medium / high (mapped from approximate cost for two).
- **Cuisine** — one or more labels; matching strategy TBD in Phase 3 (overlap / taxonomy).
- **Minimum rating** — lower bound on normalized numeric rating.
- **Additional preferences** — optional free text for soft constraints handled mainly by the LLM after filtering.

## Non-goals (milestone 1)

- User accounts, auth, or saved profiles.
- Live Zomato (or any) **production** API integration — dataset is the source of truth.
- Maps, routing, or turn-by-turn directions.
- Real-time hours, table booking integrations, or payments.
- Hosting / SLA / multi-tenant operations (local and demo-first).

## Exit criteria checklist

- [x] Written assumptions: this file + [dataset-contract.md](./dataset-contract.md).
- [x] Stack and secrets pattern: `pyproject.toml`, `.env.example`, `.gitignore`.
- [x] Local run: install package, then `milestone1 info` / `doctor` (see [README.md](../README.md)); full end-to-end **API + web** run documented when Phases 6–7 land (`recommend-run` documents readable output until then).
