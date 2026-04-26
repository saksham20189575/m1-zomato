from __future__ import annotations

import json
from collections.abc import Sequence

from milestone1.phase1_ingestion.model import Restaurant
from milestone1.phase2_preferences.model import UserPreferences

from milestone1.phase3_integration.model import PromptPayload


def _preferences_document(prefs: UserPreferences) -> dict[str, object]:
    return {
        "location": prefs.location,
        "budget_band": prefs.budget_band.value if prefs.budget_band else None,
        "cuisines": list(prefs.cuisines),
        "minimum_rating": prefs.minimum_rating,
        "additional_preferences": prefs.additional_preferences,
    }


def _escape_md_cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def _candidates_markdown_table(candidates: Sequence[Restaurant]) -> str:
    lines = [
        "| id | name | city | cuisines | rating | budget_band | approx_cost_two_inr |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for r in candidates:
        cuisines = ", ".join(r.cuisines) if r.cuisines else ""
        rating = "" if r.rating is None else f"{r.rating:g}"
        cost = "" if r.approx_cost_two is None else str(r.approx_cost_two)
        row = (
            f"| {_escape_md_cell(r.id)} | {_escape_md_cell(r.name)} | "
            f"{_escape_md_cell(r.city)} | {_escape_md_cell(cuisines)} | {rating} | "
            f"{r.budget_band.value} | {cost} |"
        )
        lines.append(row)
    return "\n".join(lines)


def build_prompt_payload(
    prefs: UserPreferences,
    candidates: Sequence[Restaurant],
) -> PromptPayload:
    """
    Build system + user messages: grounded instructions and preference + candidate context.
    """
    prefs_json = json.dumps(_preferences_document(prefs), indent=2, sort_keys=True)
    table = _candidates_markdown_table(candidates)
    allowed_ids = json.dumps([r.id for r in candidates])

    system_message = (
        "You are a restaurant recommendation assistant. "
        "You must ONLY recommend restaurants that appear in the candidate list by their "
        "exact `id` from the table. If none fit the user, say so and recommend none. "
        "Do not invent venues or IDs.\n\n"
        "Respond with a single JSON object (no markdown fences) matching this shape:\n"
        '{"rankings": [{"restaurant_id": "<id from list>", "rank": 1, "explanation": "..."}]}\n'
        "Use consecutive ranks starting at 1; include at most one entry per restaurant_id."
    )

    user_message = (
        "## User preferences (JSON)\n"
        f"{prefs_json}\n\n"
        "## Candidate restaurants\n"
        "Recommend only from these rows (markdown table). Allowed ids (JSON array):\n"
        f"{allowed_ids}\n\n"
        f"{table}\n"
    )

    return PromptPayload(system_message=system_message, user_message=user_message)
