# Google Stitch prompt — Next.js frontend (Phase 7)

Use the block below with **[Stitch (Google Labs)](https://stitch.withgoogle.com/)**—often called **Google Stitch**—or similar UI/codegen tools to generate **UI mockups**, **page layouts**, or **Next.js** starter code. The backend is a **Phase 6 FastAPI** service described in [phased-architecture.md](./phased-architecture.md); the **frontend framework is Next.js** (not Vite/CRA).

---

## Copy-paste prompt (Next.js + REST API)

Copy everything inside the code fence and paste it into Google Stitch (or your tool’s prompt field). Adjust `BASE_URL` if your API runs on another host/port.

```
You are designing and/or generating a Next.js (App Router) + TypeScript web app for a “Zomato-style” restaurant recommender. The app talks ONLY to an existing JSON HTTP API; do not call Groq or Hugging Face from the browser.

PRODUCT
- User enters preferences and sees ranked restaurant suggestions with short AI explanations.
- Tone: clear, scannable, trustworthy. Mobile-friendly first.
- Stack: Next.js 14+ (App Router), TypeScript, CSS as you prefer (Tailwind is fine). No user accounts; local demo is enough.

API (assume base URL is http://127.0.0.1:8000 in dev; use an env var NEXT_PUBLIC_API_BASE_URL in code)
- GET /health → { status: "ok", groq_configured: boolean }
- GET /api/v1/meta?load_limit=8000&cities_cap=500 → { cities: string[], truncated: boolean, load_limit_used: number, cities_cap: number } — optional for autocomplete on “location”
- POST /api/v1/recommendations
  Request JSON (align field names exactly):
  {
    "location": string (required),
    "budget": "low" | "medium" | "high" or omit / null for any,
    "cuisines": string[] (optional, empty means any),
    "minimum_rating": number | null (0–5),
    "additional_preferences": string | null (optional long text, max ~4000 chars),
    "load_limit": number | null (optional; server has default if omitted),
    "candidate_cap": number (1–200, default 30),
    "top_k": number (1–50, default 5),
    "model": string | null (optional),
    "temperature", "max_tokens", "timeout": optional; hide advanced in a collapsed “Advanced” section or omit in v1
  }
  Response JSON:
  {
    "source": "llm" | "fallback" | "no_candidates",
    "matched_count": number,
    "candidate_count": number,
    "latency_ms": number | null,
    "usage": { prompt_tokens?: number, completion_tokens?: number, ... } | null,
    "detail": string | null (e.g. fallback reason; don’t need to show prominently),
    "model": string,
    "rankings": [
      {
        "rank": number,
        "restaurant_id": string,
        "explanation": string (AI text),
        "restaurant": {
          "id": string,
          "name": string,
          "city": string,
          "cuisines": string[],
          "rating": number | null,
          "approx_cost_two_inr": number | null,
          "budget_band": "low" | "medium" | "high" | "unknown"
        } | null
      }
    ]
  }

UI REQUIREMENTS
1) Form: location (text or combobox with /meta cities as hints), budget (low/medium/high/any), cuisines (tag input or multi-select), minimum rating (slider or number), additional preferences (textarea, character hint).
2) Submit: POST /api/v1/recommendations with JSON body. Show loading state; disable double submit.
3) Results: ordered list. Each card must show: restaurant name, city, cuisines, rating, estimated cost for two in INR, budget band, and a prominent “Why” line using `explanation`. Show `rank` as order.
4) Empty / edge states (use distinct copy and layout):
   - If source is "no_candidates" OR matched_count is 0 and there are no meaningful matches: “No restaurants match your filters” + short hint to relax constraints.
   - If source is "llm" (or "fallback") but rankings is empty while candidate_count > 0: “We couldn’t justify picks from the shortlist” (LLM returned no grounded rows).
5) If source is "fallback", optional subtle notice that automated ranking was used.
6) Errors: 422 from API may return { detail: { errors: [ { field, message } ] } } — show field errors inline. Network errors: friendly message.
7) Accessibility: labels, focus states, sufficient contrast. Use fetch; CORS is configured for typical Next.js dev origin if proxy is not used; prefer Next.js rewrites in next.config to proxy /api to the Python server to avoid CORS during dev, OR document that API allows localhost origins.
8) Optional: footer with “API up?” via GET /health and groq_configured (only for dev/debug, not for end users in production).
9) Deliver: either (A) high-fidelity static UI mockups / image directions, or (B) Next.js page components + one client form component, plus types for request/response matching the JSON above.

Name the app “Milestone1 Restaurant Picks” or similar. Keep visual style modern and food-adjacent without copying Zomato’s brand.
```

---

## Optional: shorter “mockups only” prompt

Use this in Stitch if you only want **images / mockups** (no code).

```
Create 3–4 high-fidelity mobile and desktop UI mockups for a web app “Milestone1 Restaurant Picks” (Next.js). Screens: (1) preference form: location, budget low/medium/high, cuisines, min rating, extra notes, submit. (2) Loading. (3) Results: ranked cards with name, city, cuisines, star rating, ₹ cost for two, and an “AI pick” explanation. (4) Empty state: no restaurants match filters, vs empty shortlist with different message. Modern, scannable, accessible, no Zomato logo clone.
```

---

## Related docs

- [phased-architecture.md](./phased-architecture.md) — Phase 6 (API) and Phase 7 (frontend)
- [README.md](../README.md) — run `milestone1-api` and set `CORS_ORIGINS` if needed
- [problemstatement.md](./problemstatement.md) — product brief
