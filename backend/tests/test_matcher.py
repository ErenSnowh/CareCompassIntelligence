"""
Unit tests for CareCompass CaregiverMatcher Service.
Validates role filtering, distance scoring, language affinity, and benchmark reason generation.
"""

import pytest
from app.config import get_settings
from app.data.loader import DataLoader
from app.services.caregiver_matcher import CaregiverMatcher


@pytest.fixture
def data_loader():
    settings = get_settings()
    loader = DataLoader(
        triage_path=settings.triage_dataset_path,
        caregivers_path=settings.caregivers_path,
    )
    loader.load()
    return loader


@pytest.fixture
def matcher():
    return CaregiverMatcher()


def test_emergency_matches_empty(matcher, data_loader):
    # CRITICAL SAFETY RULE: Emergency 112 must NEVER match home caregivers
    matches = matcher.match(
        care_type="emergency_112",
        user_lat=28.54,
        user_lng=77.27,
        detected_language="Hindi",
        caregivers=data_loader.active_caregivers,
    )
    assert len(matches) == 0


def test_teleconsultation_matches_doctor_only(matcher, data_loader):
    matches = matcher.match(
        care_type="teleconsultation",
        user_lat=28.54,
        user_lng=77.27,
        detected_language="English",
        caregivers=data_loader.active_caregivers,
        max_results=3,
    )
    assert len(matches) > 0
    for m in matches:
        cg = data_loader.get_caregiver(m.caregiver_id)
        assert cg.role == "doctor"
        assert "★" in m.reason or "free" in m.reason


def test_lab_test_matches_phlebotomist_only(matcher, data_loader):
    matches = matcher.match(
        care_type="lab_test_home",
        user_lat=28.54,
        user_lng=77.27,
        detected_language="Hindi",
        caregivers=data_loader.active_caregivers,
        max_results=3,
    )
    assert len(matches) > 0
    for m in matches:
        cg = data_loader.get_caregiver(m.caregiver_id)
        assert cg.role == "phlebotomist"
        assert "km away" in m.reason


def test_home_nursing_matches_medic_only(matcher, data_loader):
    matches = matcher.match(
        care_type="home_nursing",
        user_lat=28.54,
        user_lng=77.27,
        detected_language="Hindi",
        caregivers=data_loader.active_caregivers,
        keywords=["wound_dressing"],
        max_results=3,
    )
    assert len(matches) > 0
    for m in matches:
        cg = data_loader.get_caregiver(m.caregiver_id)
        assert cg.role == "medic"
        assert "km away" in m.reason


def test_language_preference(matcher, data_loader):
    # Hindi patient
    matches_hi = matcher.match(
        care_type="paramedic_home_visit",
        user_lat=28.54,
        user_lng=77.27,
        detected_language="Hindi",
        caregivers=data_loader.active_caregivers,
        max_results=3,
    )
    assert len(matches_hi) > 0
    top_cg = data_loader.get_caregiver(matches_hi[0].caregiver_id)
    assert "Hindi" in top_cg.languages
