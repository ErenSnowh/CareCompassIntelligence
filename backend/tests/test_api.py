"""
Integration tests for FastAPI endpoints:
- GET /
- GET /api/v1/health
- POST /api/v1/triage (emergency red flag check)
- GET /api/v1/caregivers
"""

import pytest
from starlette.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_root_endpoint(client):
    # Front page serves interactive HTML UI
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
    assert "CareCompass AI" in response.text

    # /api serves system status JSON
    api_resp = client.get("/api")
    assert api_resp.status_code == 200
    data = api_resp.json()
    assert data["status"] == "online"
    assert "CareCompass" in data["app"]



def test_health_endpoint(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "dataset_statistics" in data
    assert data["dataset_statistics"]["triage_examples"] == 340


def test_triage_red_flag_emergency(client):
    payload = {
        "user_input": "papa ko severe chest pain ho raha hai aur breathing problem hai",
        "language": "auto",
        "location": {"lat": 28.54, "lng": 77.27},
        "conversation_history": [],
    }
    response = client.post("/api/v1/triage", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["care_type"] == "emergency_112"
    assert data["urgency"] == "emergency"
    assert len(data["red_flags"]) > 0
    assert len(data["matched_caregivers"]) == 0
    assert data["follow_up_question"] is None


def test_caregivers_list_endpoint(client):
    response = client.get("/api/v1/caregivers")
    assert response.status_code == 200
    caregivers = response.json()
    assert isinstance(caregivers, list)
    assert len(caregivers) > 0
