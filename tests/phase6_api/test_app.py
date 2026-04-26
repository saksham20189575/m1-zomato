from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from milestone1.phase1_ingestion.model import BudgetBand, Restaurant
from milestone1.phase4_llm.model import RankedRecommendation, RecommendResult
from milestone1.phase6_api.app import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def _restaurant(*, city: str = "Mumbai", rid: str = "rid1") -> Restaurant:
    return Restaurant(
        id=rid,
        name="Test Place",
        city=city,
        neighborhood="",
        address="",
        cuisines=("Chinese",),
        rating=4.1,
        approx_cost_two=600,
        approx_cost_two_raw="600",
        budget_band=BudgetBand.MEDIUM,
        votes=3,
        restaurant_type=None,
        listing_type=None,
        online_order=None,
        book_table=None,
        menu_sample=None,
        dishes_liked=None,
        url=None,
        phone=None,
    )


def test_health_ok(client: TestClient) -> None:
    r = client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert "groq_configured" in data


def test_recommend_preferences_validation_422(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "milestone1.phase6_api.service.load_restaurants",
        lambda **kw: [_restaurant(city="Mumbai")],
    )

    r = client.post(
        "/api/v1/recommendations",
        json={
            "location": "Delhi",
            "load_limit": 100,
            "candidate_cap": 10,
            "top_k": 3,
        },
    )
    assert r.status_code == 422
    body = r.json()
    assert "detail" in body
    assert "errors" in body["detail"]


def test_recommend_success_mocked(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    r1 = _restaurant(city="Mumbai", rid="a")
    monkeypatch.setattr(
        "milestone1.phase6_api.service.load_restaurants",
        lambda **kw: [r1],
    )

    pick = RankedRecommendation(
        restaurant_id=r1.id,
        rank=1,
        explanation="Nice.",
        restaurant=r1,
    )
    result = RecommendResult(
        source="llm",
        rankings=(pick,),
        matched_count=1,
        candidate_count=1,
        usage={"prompt_tokens": 1, "completion_tokens": 2},
        latency_ms=12.5,
        detail=None,
    )

    monkeypatch.setattr(
        "milestone1.phase6_api.service.recommend_with_groq",
        lambda *a, **k: result,
    )

    r = client.post(
        "/api/v1/recommendations",
        json={"location": "Mumbai", "load_limit": 50, "candidate_cap": 10, "top_k": 3},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["source"] == "llm"
    assert len(data["rankings"]) == 1
    assert data["rankings"][0]["restaurant"]["name"] == "Test Place"
    assert data["model"]


def test_meta_mocked(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "milestone1.phase6_api.service.load_restaurants",
        lambda **kw: [_restaurant(city="Mumbai"), _restaurant(city="Delhi", rid="b")],
    )
    r = client.get("/api/v1/meta", params={"load_limit": 100, "cities_cap": 10})
    assert r.status_code == 200
    data = r.json()
    assert data["cities"] == ["Delhi", "Mumbai"]
    assert data["truncated"] is False


def test_recommend_body_validation_candidate_cap(client: TestClient) -> None:
    r = client.post(
        "/api/v1/recommendations",
        json={"location": "X", "candidate_cap": 0},
    )
    assert r.status_code == 422
