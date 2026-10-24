"""
Unit tests for CareCompass DataLoader.
Validates loading of 340 triage examples and 60 caregiver records.
"""

from pathlib import Path
from app.config import get_settings
from app.data.loader import DataLoader


def test_data_loader_initialization():
    settings = get_settings()
    loader = DataLoader(
        triage_path=settings.triage_dataset_path,
        caregivers_path=settings.caregivers_path,
    )
    loader.load()

    assert len(loader.triage_data) == 340
    assert len(loader.caregivers) == 60
    assert len(loader.active_caregivers) > 0


def test_data_loader_statistics():
    settings = get_settings()
    loader = DataLoader(
        triage_path=settings.triage_dataset_path,
        caregivers_path=settings.caregivers_path,
    )
    loader.load()
    stats = loader.get_statistics()

    assert stats["triage_examples"] == 340
    assert stats["caregivers_total"] == 60
    assert "home_nursing" in stats["care_type_distribution"]
    assert "emergency_112" in stats["care_type_distribution"]
    assert "doctor" in stats["caregiver_role_distribution"]
    assert "medic" in stats["caregiver_role_distribution"]
    assert "phlebotomist" in stats["caregiver_role_distribution"]


def test_get_caregiver_by_id():
    settings = get_settings()
    loader = DataLoader(
        triage_path=settings.triage_dataset_path,
        caregivers_path=settings.caregivers_path,
    )
    loader.load()

    cg = loader.get_caregiver("CG_001")
    assert cg is not None
    assert cg.caregiver_id == "CG_001"
    assert len(cg.languages) > 0
    assert len(cg.skills) > 0
    assert cg.max_radius_km > 0
