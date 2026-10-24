"""
Unit tests for CareCompass Settings and Configuration.
"""

from app.config import get_settings


def test_settings_defaults():
    settings = get_settings()
    assert settings.app_name == "CareCompass AI"
    assert settings.app_version == "0.1.0"
    assert settings.app_port == 8000
    assert settings.confidence_threshold == 0.6
    assert settings.max_matched_caregivers == 3
    assert settings.weight_language + settings.weight_distance + settings.weight_skill <= 1.0
