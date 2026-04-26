# Dataset contract (v1)

**Source:** [ManikaSaini/zomato-restaurant-recommendation](https://huggingface.co/datasets/ManikaSaini/zomato-restaurant-recommendation) on the Hugging Face Hub.

**Verified split:** `train` (streaming iterator used during Phase 0 verification).

**Pinned revision (Phase 1):** `5738e9eda2fad49ad51c6e0ed26e761d9b947133` — matches `milestone1.ingestion.constants.DATASET_REVISION` for reproducible loads.

**Row count (Hub):** ~51k rows (subject to upstream changes).

## Raw columns → internal fields (v1 mapping)

Internal names are targets for the canonical model in Phase 1. Until then, this table is the **contract** for ingestion and prompts.

| Hugging Face column | Internal field | v1 notes |
|--------------------|----------------|---------|
| `name` | `name` | Required for display and grounding. |
| `listed_in(city)` | `city` | Primary geography for “location” filters (exact policy in Phase 3). |
| `location` | `neighborhood` | Finer-grained area within city; optional for filtering and prompts. |
| `address` | `address` | Optional context in prompts / UI. |
| `cuisines` | `cuisines` | Parse to list of strings (separators may vary). |
| `approx_cost(for two people)` | `approx_cost_two` | Normalize to integer band or enum for budget matching. |
| `rate` | `rating_raw` | Parse to float; handle `"-"`, `"NEW"`, `"4.2/5"` style strings in Phase 1. |
| `votes` | `votes` | Optional tie-break / quality signal (integer). |
| `rest_type` | `restaurant_type` | e.g. Casual Dining — soft signal for LLM. |
| `listed_in(type)` | `listing_type` | Hub metadata; optional filter. |
| `online_order` | `online_order` | Boolean-like flag if parseable. |
| `book_table` | `book_table` | Boolean-like flag if parseable. |
| `menu_item` | `menu_sample` | Long text; truncate in prompts (see edge cases). |
| `dish_liked` | `dishes_liked` | Free text; optional prompt context. |
| `reviews_list` | `reviews_blob` | Large / structured text; **exclude or heavily truncate** in v1 prompts unless explicitly needed. |
| `phone` | `phone` | Optional; privacy-sensitive — avoid logging. |
| `url` | `url` | Optional link out in UI later. |

## Stability

Upstream schema renames would break ingestion. Mitigation: a dataset **revision** is pinned in `src/milestone1/phase1_ingestion/constants.py`, and `assert_hub_row_schema` runs on the first streamed row.

## Internal record (Phase 1 target)

A single in-memory type (e.g. `Restaurant`) should implement at minimum:

`id`, `name`, `city`, `neighborhood`, `cuisines`, `rating`, `budget_band`, `approx_cost_two_raw`, plus optional fields needed for filtering and LLM context.

Stable `id` should be derived (hash or row index after dedupe) if the Hub provides no unique key.
