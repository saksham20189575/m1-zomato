from __future__ import annotations

from milestone1.phase4_llm.model import RankedRecommendation, RecommendResult

from milestone1.phase5_output.empty_copy import (
    EmptyPresentationKind,
    empty_state_body,
    empty_state_headline,
    presentation_kind,
)


def _format_inr(amount: int | None) -> str:
    if amount is None:
        return "unknown"
    return f"₹{amount}"


def _format_rating(value: float | None) -> str:
    if value is None:
        return "not rated"
    return f"{value:g} / 5"


def render_ranking_markdown(item: RankedRecommendation) -> str:
    """One recommendation block: name, cuisine, rating, estimated cost, explanation."""
    r = item.restaurant
    if r is not None:
        name = r.name
        cuisines = ", ".join(r.cuisines) if r.cuisines else "—"
        rating = _format_rating(r.rating)
        cost = _format_inr(r.approx_cost_two)
        band = r.budget_band.value
        lines = [
            f"### {item.rank}. {name}",
            f"- **Cuisines:** {cuisines}",
            f"- **Rating:** {rating}",
            f"- **Estimated cost (two):** {cost} ({band})",
            f"- **Why:** {item.explanation}",
        ]
        return "\n".join(lines)
    return "\n".join(
        [
            f"### {item.rank}. (unknown venue `{item.restaurant_id}`)",
            f"- **Why:** {item.explanation}",
        ]
    )


def render_ranking_plain(item: RankedRecommendation) -> str:
    r = item.restaurant
    if r is not None:
        cuisines = ", ".join(r.cuisines) if r.cuisines else "—"
        rating = _format_rating(r.rating)
        cost = _format_inr(r.approx_cost_two)
        band = r.budget_band.value
        lines = [
            f"{item.rank}. {r.name}",
            f"   Cuisines: {cuisines}",
            f"   Rating: {rating}",
            f"   Estimated cost (two): {cost} ({band})",
            f"   Why: {item.explanation}",
        ]
        return "\n".join(lines)
    return f"{item.rank}. id={item.restaurant_id}\n   Why: {item.explanation}"


def render_report_markdown(result: RecommendResult) -> str:
    """Full markdown report including empty states and optional fallback banner."""
    kind = presentation_kind(result)
    parts: list[str] = ["# Recommendations", ""]

    if result.source == "fallback" and result.detail:
        parts.extend(
            [
                "> **Note:** Results use automated fallback ranking (model error or invalid output).",
                "",
            ]
        )

    if kind is not EmptyPresentationKind.RESULTS:
        title = empty_state_headline(kind)
        body = empty_state_body(kind)
        assert title and body
        parts.extend([f"## {title}", "", body, ""])
        parts.extend(
            [
                "---",
                "",
                f"*Filter matches (pre-cap):* **{result.matched_count}** · "
                f"*Candidates sent to model:* **{result.candidate_count}**",
                "",
            ]
        )
        return "\n".join(parts).rstrip() + "\n"

    for item in result.rankings:
        parts.append(render_ranking_markdown(item))
        parts.append("")

    parts.extend(
        [
            "---",
            "",
            f"*Filter matches (pre-cap):* **{result.matched_count}** · "
            f"*Candidates sent to model:* **{result.candidate_count}** · "
            f"*Source:* **{result.source}**",
            "",
        ]
    )
    return "\n".join(parts).rstrip() + "\n"


def render_report_plain(result: RecommendResult) -> str:
    kind = presentation_kind(result)
    lines: list[str] = ["Recommendations", ""]

    if result.source == "fallback" and result.detail:
        lines.extend(["Note: automated fallback ranking was used.", ""])

    if kind is not EmptyPresentationKind.RESULTS:
        title = empty_state_headline(kind)
        body = empty_state_body(kind)
        assert title and body
        lines.extend([title, "", body, ""])
        lines.extend(
            [
                f"Filter matches (pre-cap): {result.matched_count} · "
                f"Candidates sent to model: {result.candidate_count}",
                "",
            ]
        )
        return "\n".join(lines).rstrip() + "\n"

    for item in result.rankings:
        lines.append(render_ranking_plain(item))
        lines.append("")

    lines.extend(
        [
            f"Filter matches (pre-cap): {result.matched_count} · "
            f"Candidates: {result.candidate_count} · Source: {result.source}",
            "",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"
