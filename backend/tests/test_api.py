"""
API-layer tests. These run WITHOUT any API key, so the explanation always comes
from the deterministic fallback (no network). If FastAPI isn't installed, the
whole module is skipped so the pure-engine test suite still runs standalone.
"""
from __future__ import annotations

import os

import pytest

# Ensure the LLM path is never taken in tests, regardless of the environment.
os.environ.pop("ANTHROPIC_API_KEY", None)

fastapi = pytest.importorskip("fastapi")
from fastapi.testclient import TestClient  # noqa: E402

from app.api import app  # noqa: E402

client = TestClient(app)


class TestHealth:
    def test_health_ok(self):
        r = client.get("/api/health")
        assert r.status_code == 200
        body = r.json()
        assert body["status"] == "ok"
        assert body["llm_enabled"] is False  # no key in tests
        assert body["activities"] >= 10
        assert body["free_zones"] >= 8


class TestActivities:
    def test_list_activities(self):
        r = client.get("/api/activities")
        assert r.status_code == 200
        acts = r.json()["activities"]
        ids = {a["id"] for a in acts}
        assert "commodities_trading" in ids
        assert "restaurant_fnb" in ids
        # required display fields present
        for a in acts:
            assert {"id", "label", "categories", "mainland_required", "regulated"} <= set(a)


class TestFreeZones:
    def test_list_free_zones(self):
        r = client.get("/api/free-zones")
        assert r.status_code == 200
        ids = {z["id"] for z in r.json()["free_zones"]}
        assert {"dmcc", "difc", "ifza"} <= ids


class TestEvaluate:
    def test_free_zone_flow(self):
        r = client.post("/api/evaluate", json={
            "activity_id": "commodities_trading",
            "target_market": "international",
            "employee_visa_count": 2,
            "budget_aed": 50000,
        })
        assert r.status_code == 200
        body = r.json()
        assert body["setup_type"] == "free_zone"
        assert body["zone_shortlist"][0]["zone_id"] == "dmcc"
        # cost bands serialized as 2-element lists
        cost = body["zone_shortlist"][0]["cost"]["first_year_total_aed"]
        assert isinstance(cost, list) and len(cost) == 2
        # explanation attached, deterministic fallback (no key)
        assert body["explanation"]["source"] == "fallback"
        assert body["explanation"]["model"] is None
        assert "DMCC" in body["explanation"]["text"]

    def test_mainland_flow(self):
        r = client.post("/api/evaluate", json={
            "activity_id": "restaurant_fnb",
            "target_market": "local_uae",
        })
        assert r.status_code == 200
        body = r.json()
        assert body["setup_type"] == "mainland"
        assert body["zone_shortlist"] == []

    def test_explanation_can_be_disabled(self):
        r = client.post("/api/evaluate", json={
            "activity_id": "it_software",
            "explain": False,
        })
        assert r.status_code == 200
        assert "explanation" not in r.json()

    def test_unknown_activity_rejected(self):
        r = client.post("/api/evaluate", json={"activity_id": "nope"})
        assert r.status_code == 422  # pydantic validation error

    def test_negative_visa_count_rejected(self):
        r = client.post("/api/evaluate", json={
            "activity_id": "it_software",
            "employee_visa_count": -1,
        })
        assert r.status_code == 422

    def test_every_reason_has_citation_in_payload(self):
        r = client.post("/api/evaluate", json={
            "activity_id": "general_trading",
            "employee_visa_count": 2,
            "budget_aed": 30000,
        })
        body = r.json()
        reasons = body["setup_type_reasons"] + body["ownership_reasons"]
        for z in body["zone_shortlist"]:
            reasons += z["match_reasons"]
        for reason in reasons:
            assert reason["citation"]["rule_id"]
            assert reason["citation"]["source_ref"]
