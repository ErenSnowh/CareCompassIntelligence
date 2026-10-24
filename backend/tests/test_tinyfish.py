"""
Unit tests for TinyFishService integration.
Validates clinical knowledge grounding and live provider verification.
"""

import pytest
from starlette.testclient import TestClient
from app.main import app
from app.services.tinyfish_service import TinyFishService


@pytest.fixture
def tinyfish():
    return TinyFishService()


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.mark.asyncio
async def test_search_medical_context(tinyfish):
    # Fever guidelines
    guideline = await tinyfish.search_medical_context("fever and cough for 2 days")
    assert guideline is not None
    assert "temperature" in guideline.lower() or "hydration" in guideline.lower()

    # Wound dressing guidelines
    guideline_wound = await tinyfish.search_medical_context("post-surgery wound dressing change")
    assert guideline_wound is not None
    assert "aseptic" in guideline_wound.lower() or "dressing" in guideline_wound.lower()


@pytest.mark.asyncio
async def test_verify_caregiver_credentials(tinyfish):
    res = await tinyfish.verify_caregiver_credentials("CG_001", "MED-CG_001-2026")
    assert res["verified"] is True
    assert "caregiver_id" in res
    assert "National Medical Commission" in res["verification_source"] or "Nursing" in res["verification_source"]


def test_api_verify_caregiver_endpoint(client):
    response = client.get("/api/v1/caregivers/CG_001/verify")
    assert response.status_code == 200
    data = response.json()
    assert "caregiver" in data
    assert "verification" in data
    assert data["verification"]["verified"] is True


def test_api_medical_grounding_endpoint(client):
    response = client.get("/api/v1/medical-grounding?query=wound%20dressing%20care")
    assert response.status_code == 200
    data = response.json()
    assert "guidelines" in data
    assert data["guidelines"] is not None


def test_end_to_end_triage_with_tinyfish(client):
    payload = {
        "user_input": "Grandmother has a bedsore that needs dressing",
        "language": "auto",
        "location": {"lat": 28.54, "lng": 77.27},
        "conversation_history": [],
    }
    response = client.post("/api/v1/triage", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["care_type"] == "home_nursing"
    assert data["urgency"] == "same_day"
    assert data["medical_context"] is not None
    assert data["confidence"] > 0.5
    assert len(data["matched_caregivers"]) > 0
