from __future__ import annotations

from milestone1.phase1_ingestion.model import BudgetBand, Restaurant
from milestone1.phase2_preferences.model import UserPreferences
from milestone1.phase3_integration.model import PromptPayload
from milestone1.phase4_llm.errors import GroqTransportError
from milestone1.phase4_llm.groq_client import GroqCompletion
from milestone1.phase4_llm.recommend import recommend_with_groq


def _r(rid: str, city: str = "Mumbai") -> Restaurant:
    return Restaurant(
        id=rid,
        name=f"N-{rid}",
        city=city,
        neighborhood="",
        address="",
        cuisines=("Chinese",),
        rating=4.0,
        approx_cost_two=500,
        approx_cost_two_raw="500",
        budget_band=BudgetBand.LOW,
        votes=1,
        restaurant_type=None,
        listing_type=None,
        online_order=None,
        book_table=None,
        menu_sample=None,
        dishes_liked=None,
        url=None,
        phone=None,
    )


def _prefs() -> UserPreferences:
    return UserPreferences(
        location="Mumbai",
        budget_band=None,
        cuisines=(),
        minimum_rating=None,
        additional_preferences=None,
    )


def test_no_candidates_without_llm() -> None:
    rows = [_r("a", city="Delhi")]
    res = recommend_with_groq(rows, _prefs(), groq_caller=lambda p: GroqCompletion(text="{}", usage=None, model="x"))
    assert res.source == "no_candidates"
    assert res.rankings == ()


def test_llm_path_parses_and_enriches() -> None:
    rows = [_r("id1"), _r("id2")]
    good = (
        '{"rankings": ['
        '{"restaurant_id": "id2", "rank": 1, "explanation": "second first"},'
        '{"restaurant_id": "id1", "rank": 2, "explanation": "first second"}'
        "]}"
    )

    def _caller(p: PromptPayload) -> GroqCompletion:
        assert "rankings" in p.system_message
        return GroqCompletion(text=good, usage={"prompt_tokens": 1, "completion_tokens": 2}, model="m")

    res = recommend_with_groq(rows, _prefs(), top_k=5, groq_caller=_caller)
    assert res.source == "llm"
    assert len(res.rankings) == 2
    assert res.rankings[0].restaurant_id == "id2"
    assert res.rankings[0].restaurant is not None
    assert res.rankings[0].restaurant.name == "N-id2"
    assert res.usage == {"prompt_tokens": 1, "completion_tokens": 2}


def test_fallback_on_transport_error() -> None:
    rows = [_r("id1")]

    def _caller(p: PromptPayload) -> GroqCompletion:
        raise GroqTransportError("down", status_code=503)

    res = recommend_with_groq(rows, _prefs(), top_k=3, groq_caller=_caller)
    assert res.source == "fallback"
    assert len(res.rankings) == 1
    assert res.rankings[0].restaurant_id == "id1"
    assert "fallback" in res.rankings[0].explanation.lower()
    assert res.detail == "down"


def test_fallback_on_invalid_json() -> None:
    rows = [_r("id1")]

    def _caller(p: PromptPayload) -> GroqCompletion:
        return GroqCompletion(text="NOT JSON", usage=None, model="m")

    res = recommend_with_groq(rows, _prefs(), top_k=2, groq_caller=_caller)
    assert res.source == "fallback"
    assert res.rankings[0].restaurant_id == "id1"


def test_top_k_truncates_llm_rankings() -> None:
    rows = [_r("a"), _r("b"), _r("c")]
    raw = (
        '{"rankings": ['
        '{"restaurant_id": "a", "rank": 1, "explanation": "1"},'
        '{"restaurant_id": "b", "rank": 2, "explanation": "2"},'
        '{"restaurant_id": "c", "rank": 3, "explanation": "3"}'
        "]}"
    )

    def _caller(p: PromptPayload) -> GroqCompletion:
        return GroqCompletion(text=raw, usage=None, model="m")

    res = recommend_with_groq(rows, _prefs(), top_k=2, groq_caller=_caller)
    assert res.source == "llm"
    assert len(res.rankings) == 2
    assert {r.restaurant_id for r in res.rankings} == {"a", "b"}
