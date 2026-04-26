# Detailed edge cases

This document lists **edge cases and failure modes** for the restaurant recommendation project, aligned with [problemstatement.md](./problemstatement.md) and [phased-architecture.md](./phased-architecture.md). Use it for **requirements**, **manual QA**, and **automated tests** (fixtures and assertions).

**Legend**

- **Trigger:** what provokes the case.  
- **Expected:** acceptable product behavior (choose one policy and document it in code/README).  
- **Phase:** primary place in [phased-architecture.md](./phased-architecture.md) where the case matters.

---

## Phase 0 — Scope, environment, and operations

| ID | Trigger | Expected | Phase |
|----|---------|----------|-------|
| EC-0.1 | No API key / wrong key for the LLM provider | Clear error before or at first LLM call; no silent hang; no key printed in logs | 0, 4 |
| EC-0.2 | Hugging Face or dataset URL unreachable (offline, firewall, DNS) | User-visible failure loading data; optional retry/backoff; distinguish “network” vs “bad dataset revision” | 0, 1 |
| EC-0.3 | Dataset revision or schema changed upstream (column rename, split change) | Fail fast with message pointing to schema mismatch; keep a pinned revision in config if you need stability | 0, 1 |
| EC-0.4 | Running on a machine with very little RAM / disk | Document minimums; stream or sample rows for dev; avoid loading full parquet into memory twice | 0, 1 |
| EC-0.5 | User runs app from wrong working directory (relative paths to cache/config) | Resolve paths from project root or env; predictable error if cache file missing | 0 |

---

## Phase 1 — Data ingestion and canonical model

| ID | Trigger | Expected | Phase |
|----|---------|----------|-------|
| EC-1.1 | Empty dataset (zero rows after load) | Cannot recommend; message: data unavailable or empty; no LLM call with empty candidates | 1, 3, 5 |
| EC-1.2 | Corrupt / truncated download (partial file) | Parse error caught; message suggests re-download; no half-valid silent state | 1 |
| EC-1.3 | Duplicate rows (same restaurant repeated) | Dedupe by stable key (name+location+lat/long if present) **or** keep duplicates but risk double recommendations—pick one policy and test it | 1, 3 |
| EC-1.4 | Duplicate **display names** in different locations | Both rows valid; internal unique `id` in prompts so LLM and UI do not confuse them | 1, 3, 4 |
| EC-1.5 | Missing **restaurant name** | Exclude row or mark “Unknown name”—never send unnamed rows to UI without a fallback label | 1, 5 |
| EC-1.6 | Missing **location** | Row cannot satisfy location filter; either drop at ingest or exclude in filter; document | 1, 3 |
| EC-1.7 | Missing **rating** | Define policy: treat as worst rating, exclude from min-rating filter, or impute—**do not** compare `None` as a number | 1, 3 |
| EC-1.8 | Rating stored as string (`"4.2"`, `"4.2/5"`, `"**"`) | Normalize to numeric or sentinel; invalid → exclude or “unknown rating” bucket | 1 |
| EC-1.9 | Missing **cost** / cost not mappable to low/medium/high | Exclude from strict budget filter **or** map to “unknown” and only pass to LLM with explicit “cost unknown” flag | 1, 3 |
| EC-1.10 | Cost as wide range, currency symbols, or inconsistent units | Normalize to your canonical enum or numeric band; reject unparseable with metric in logs | 1 |
| EC-1.11 | **Cuisine** missing or empty string | Treat as “cuisine unknown”; cuisine filter must not false-match empty | 1, 3 |
| EC-1.12 | Multiple cuisines in one cell (`"Italian, Chinese"`, `"North Indian | Chinese"`) | Parse to list; match if **any** overlaps user cuisine (unless you define “all must match”) | 1, 3 |
| EC-1.13 | Fusion labels (`"Asian Fusion"`) vs user `"Chinese"` | Document overlap rules (substring, taxonomy map, or LLM-only soft match after filter) | 1, 3 |
| EC-1.14 | Unicode / emoji in names or addresses | UTF-8 end-to-end; UI/CLI renders without mojibake; prompts remain valid JSON/markdown | 1, 5 |
| EC-1.15 | Extremely long text fields | Truncate for prompt with ellipsis + char cap; keep full string for UI if needed | 1, 3 |
| EC-1.16 | Numeric fields with outliers (rating 10, cost absurd) | Clamp, exclude, or flag; do not crash sorting | 1, 3 |

---

## Phase 2 — User preferences and validation

| ID | Trigger | Expected | Phase |
|----|---------|----------|-------|
| EC-2.1 | All-whitespace or empty required fields (if any are required) | Validation error; do not call filter/LLM with ambiguous prefs | 2 |
| EC-2.2 | **Location** not present in dataset (typo, foreign city, neighborhood not in data) | Message: unknown or unsupported location; suggest fuzzy match **or** list valid cities from data | 2, 5 |
| EC-2.3 | Location casing / spelling variants (`"delhi"` vs `"Delhi"`, `"Bengaluru"` vs `"Bangalore"`) | Normalize with alias map or casefold + canonical vocabulary built from data | 2, 3 |
| EC-2.4 | **Budget** value outside allowed enum (`"luxury"`, `"$$$"`, numeric typo) | Reject with allowed values **or** map synonyms explicitly | 2 |
| EC-2.5 | **Cuisine** list empty meaning “any cuisine” vs “invalid” | Define UX: e.g. empty = any; distinguish from “user cleared field” in forms | 2, 3 |
| EC-2.6 | **Minimum rating** negative, > max scale, non-numeric | Validation error with allowed range (match dataset scale, e.g. 0–5) | 2 |
| EC-2.7 | Minimum rating **exactly** at boundary (e.g. 4.0) | Inclusive/exclusive rule documented; consistent filter and LLM wording | 2, 3 |
| EC-2.8 | **Conflicting preferences** (e.g. very low budget + “tasting menu” in free text) | Still return grounded list if filters pass; LLM may explain tradeoffs—do not crash | 2, 4 |
| EC-2.9 | **Additional preferences** extremely long (paste attack, megabytes) | Max length; truncate with notice; rate-limit if HTTP API | 2 |
| EC-2.10 | Additional text with **prompt-injection style** content (“ignore previous instructions…”) | Treat as untrusted user text; system prompt precedence; never execute instructions inside user blobs | 2, 3, 4 |
| EC-2.11 | Additional text in **non-English** while model/prompt assumes English | Either detect and respond bilingually **or** document English-only; avoid silent garbage output | 2, 4, 5 |

---

## Phase 3 — Integration: filters, candidate cap, prompts

| ID | Trigger | Expected | Phase |
|----|---------|----------|-------|
| EC-3.1 | **Zero candidates** after deterministic filters | No LLM call **or** LLM call with explicit “no candidates” payload—pick one; user sees “no matches” with hint to relax filters | 3, 5 |
| EC-3.2 | **Very large** candidate set (thousands pass location only) | Apply cap (e.g. 15–50); deterministic pre-sort before truncation so results are reproducible | 3 |
| EC-3.3 | Cap cuts off **better** restaurants lower in table order | Document: pre-sort by (rating, votes, cost fit) before taking top *N* | 3 |
| EC-3.4 | **Cuisine filter** too strict → zero rows | Same as EC-3.1; optional “did you mean” or “try related cuisines” | 3, 5 |
| EC-3.5 | **Budget filter** excludes rows with unknown cost | User understands why count dropped; optional toggle “include unknown cost” | 3 |
| EC-3.6 | **Location matching** ambiguous (substring hits wrong city) | Prefer exact normalized city; avoid naive `contains` on short tokens | 3 |
| EC-3.7 | User selects cuisine that exists only as part of fusion label | Either taxonomy mapping or softer post-filter retrieval for LLM | 3 |
| EC-3.8 | **Ties** on pre-sort (same rating/cost) | Stable secondary key (name, id) so order is reproducible across runs | 3 |
| EC-3.9 | Prompt near **context limit** (many columns × *N* rows) | Trim columns in prompt; keep id, name, location, cuisines, rating, cost, one-line summary | 3, 4 |
| EC-3.10 | Candidate JSON/markdown includes characters that break fences (` ``` ` in data) | Escape or strip; never let raw data terminate prompt blocks early | 3, 4 |

---

## Phase 4 — LLM: grounding, parsing, resilience

| ID | Trigger | Expected | Phase |
|----|---------|----------|-------|
| EC-4.1 | Model **hallucinates** a restaurant not in the candidate list | Parser rejects; retry with stricter prompt **or** drop invalid entries; if none left → fallback | 4, 5 |
| EC-4.2 | Model returns **duplicate** restaurants in ranked list | Deduplicate by id; preserve best rank/explanation | 4 |
| EC-4.3 | Model returns valid names but **wrong ids** or mismatched pairing | Join by canonical id from prompt, not by name alone; reject orphan ids | 4 |
| EC-4.4 | Model returns **empty** list despite non-empty candidates | Retry once; then deterministic top-*k* with template explanation **or** honest “model returned no ranking” | 4, 5 |
| EC-4.5 | Model returns **partial JSON** (truncated mid-stream) | Parser error path; retry with lower *k* or tighter max tokens; fallback | 4 |
| EC-4.6 | Model wraps JSON in markdown fences or adds commentary | Strip fences; extract first JSON object; log raw response on failure | 4 |
| EC-4.7 | Model returns **wrong schema** (missing `explanation`, wrong types) | Validation error; retry with one-shot example in prompt; fallback | 4 |
| EC-4.8 | Model ranks **fewer** than requested top-*k* | UI shows available; padding only if policy allows template text | 4, 5 |
| EC-4.9 | **Timeout** | User-visible timeout message; fallback to deterministic order | 4, 5 |
| EC-4.10 | **429 / quota** from provider | Backoff + clear message; optional queue | 4 |
| EC-4.11 | **401 / 403** | Auth misconfiguration message; no infinite retry | 4 |
| EC-4.12 | **5xx** from provider | Limited retries with jitter; then fallback | 4 |
| EC-4.13 | Model output language inconsistent | If product is English-only, add instruction and verify first line | 4, 5 |
| EC-4.14 | **Explanation** empty string or generic (“good restaurant”) | Optional quality check: retry or flag in UI “weak explanation” | 4, 5 |
| EC-4.15 | Explanation **leaks** system prompt or tool instructions | Strip known prefixes; do not echo secrets; log alert if pattern detected | 4, 5 |

---

## Phase 5 — Output display and UX

| ID | Trigger | Expected | Phase |
|----|---------|----------|-------|
| EC-5.1 | Filter empty vs LLM failure vs parse failure | **Three distinct** empty states (per architecture): no matches vs service error vs “could not parse model output” | 5 |
| EC-5.2 | Restaurant **name** contains markup-like characters (`<`, `&`) | Safe rendering in HTML; plain text in CLI | 5 |
| EC-5.3 | **Very long** AI explanation | Wrap/truncate with “read more”; do not break layout | 5 |
| EC-5.4 | Rating/cost missing on a row that still appears (fallback path) | Show “N/A” or “unknown”; do not blank the card | 5 |
| EC-5.5 | Optional **summary** of the set enabled and model omits it | UI hides summary section or shows placeholder | 5 |
| EC-5.6 | User reruns same query immediately | Idempotent-ish behavior: same seed/candidate order yields same deterministic part; LLM may vary—document | 5 |

---

## Phase 6 — Hardening, testing, and cross-cutting

| ID | Trigger | Expected | Phase |
|----|---------|----------|-------|
| EC-6.1 | Golden tests with **frozen** fake LLM responses | Parser and join logic covered without live API | 6 |
| EC-6.2 | Regression when dataset sample in repo is tiny | CI uses fixture subset; smoke test still runs | 6 |
| EC-6.3 | **Logging** accidentally includes full prompts with PII | Redact addresses/names in logs or log only ids and counts | 5, 6 |
| EC-6.4 | **Cost/latency**: user sets tiny candidate cap vs huge cap | Document tradeoff; enforce hard max cap in code | 3, 6 |
| EC-6.5 | Future **API** wrapper: concurrent requests | No global mutable singleton for dataset without locking; document thread safety | 0, 6 |

---

## Problem-statement coverage checklist

Use this to confirm you did not miss a workflow area from [problemstatement.md](./problemstatement.md).

| Workflow area | Edge-case groups above |
|---------------|-------------------------|
| Data ingestion | EC-1.*, EC-0.2–0.3 |
| User input | EC-2.* |
| Integration (filter + format + prompt) | EC-3.* |
| Recommendation engine (LLM) | EC-4.* |
| Output display | EC-5.* |

---

## Suggested test matrix (minimal)

1. **Happy path:** known city + cuisine + budget + min rating → non-empty candidates → valid JSON → all fields render.  
2. **No candidates:** impossible combination → EC-3.1 / EC-5.1 branch.  
3. **Huge match set:** location-only query → cap + stable sort (EC-3.2–3.3).  
4. **Bad data row:** missing rating/cost in fixture → no crash (EC-1.7–1.9).  
5. **LLM offline:** force error → fallback or clear error (EC-4.9–4.12).  
6. **Hallucination:** fixture response with bogus name → reject/repair (EC-4.1).  
7. **Injection string** in additional prefs → output still only from candidates (EC-2.10 + EC-4.1).

---

## Document maintenance

When you change **filter rules**, **schema**, or **prompt/output contract**, update the relevant EC rows and the suggested matrix so QA and graders stay aligned with the architecture’s **hard constraints vs LLM responsibilities** split.
