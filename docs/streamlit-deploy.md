# Phase 8 — Streamlit app (run & deploy)

The Streamlit UI lives in `src/milestone1/phase8_streamlit/app.py` and is started from the repo root via **`streamlit_app.py`** so [Streamlit Community Cloud](https://streamlit.io/cloud) can use a stable main file path.

## Local run

1. Install the package and Streamlit extra:

   ```bash
   cd /path/to/milestone1
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -e ".[streamlit]"
   ```

2. Put **`GROQ_API_KEY`** in the project root **`.env`** (same as Phase 6 / README). Optional: **`GROQ_MODEL`**.

3. Start the app:

   ```bash
   streamlit run streamlit_app.py
   ```

   Open the URL Streamlit prints (usually `http://localhost:8501`).

4. Pick a **location**, set optional filters, then **Get recommendations**. The app calls the same in-process stack as **`POST /api/v1/recommendations`** (`recommend_to_response`).

## Streamlit Community Cloud

1. Push the repo to GitHub (include `streamlit_app.py`, `pyproject.toml`, `src/`).

2. In Cloud: **New app** → pick repo → **Main file path:** `streamlit_app.py`.

3. **Python version:** 3.11+ (match `requires-python` in `pyproject.toml`).

4. **Secrets** (app settings → Secrets). Minimal TOML:

   ```toml
   GROQ_API_KEY = "your-key-here"
   ```

   Optional:

   ```toml
   GROQ_MODEL = "llama-3.3-70b-versatile"
   ```

5. **Dependencies:** Cloud must install the project with the Streamlit extra. If the UI offers a **requirements file**, point it at [`requirements-streamlit.txt`](../requirements-streamlit.txt) in this repo, or set the advanced install command to:

   ```bash
   pip install -e ".[streamlit]"
   ```

6. **Cold starts / limits:** Free tier apps sleep when idle. First load may time out if Hugging Face + model are slow—try a lower **Dataset rows to scan** (`load_limit`) in the sidebar (e.g. 2000–4000).

## Troubleshooting

| Symptom | What to check |
|--------|----------------|
| “Groq API key: ✗ missing” | `.env` locally, or Cloud **Secrets** `GROQ_API_KEY` |
| “No cities returned…” | Raise `load_limit`; confirm outbound network to Hugging Face |
| 422 / validation errors | Location must match a city from the loaded sample |
| Model errors | `GROQ_MODEL` spelling; Groq account limits |
