"""
CareCompass AI — Enumerations
Defines all enum types for the care triage system.
Matches the exact API contract from the Sanocare problem statement.
"""

from enum import Enum


class CareType(str, Enum):
    """Type of care recommended by the triage system."""
    PARAMEDIC_HOME_VISIT = "paramedic_home_visit"
    HOME_NURSING = "home_nursing"
    LAB_TEST_HOME = "lab_test_home"
    TELECONSULTATION = "teleconsultation"
    EMERGENCY_112 = "emergency_112"


class Urgency(str, Enum):
    """Urgency level of the care recommendation."""
    EMERGENCY = "emergency"
    SAME_DAY = "same_day"
    SCHEDULED = "scheduled"


class RedFlag(str, Enum):
    """
    Controlled vocabulary for life-threatening red flags.
    ANY red flag → care_type=emergency_112, urgency=emergency, matched_caregivers=[].
    """
    CHEST_PAIN = "chest_pain"
    BREATHLESSNESS = "breathlessness"
    UNCONSCIOUSNESS = "unconsciousness"
    SEVERE_BLEEDING = "severe_bleeding"
    STROKE_SYMPTOMS = "stroke_symptoms"
    SEIZURE = "seizure"
    HIGH_FEVER_INFANT = "high_fever_infant"
    SUICIDAL_IDEATION = "suicidal_ideation"
    SEVERE_DEHYDRATION = "severe_dehydration"


class CaregiverRole(str, Enum):
    """Roles available in the caregiver roster."""
    MEDIC = "medic"
    DOCTOR = "doctor"
    PHLEBOTOMIST = "phlebotomist"


class CaregiverTier(str, Enum):
    """Tier levels for medics (higher tiers unlock more procedures)."""
    BASE = "base"
    STANDARD = "standard"
    ADVANCED = "advanced"
    EXPERT = "expert"


class DetectedLanguage(str, Enum):
    """Languages detected in user input."""
    ENGLISH = "English"
    HINDI = "Hindi"
    HINGLISH = "Hinglish"


# --- Mapping Constants ---

# Maps care_type → which caregiver roles are eligible
CARE_ROLE_MAP: dict[CareType, list[CaregiverRole]] = {
    CareType.PARAMEDIC_HOME_VISIT: [CaregiverRole.MEDIC],
    CareType.HOME_NURSING: [CaregiverRole.MEDIC],
    CareType.LAB_TEST_HOME: [CaregiverRole.PHLEBOTOMIST],
    CareType.TELECONSULTATION: [CaregiverRole.DOCTOR],
    CareType.EMERGENCY_112: [],  # No caregiver matching for emergencies
}

# Maps care_type → relevant skills to look for
CARE_SKILL_MAP: dict[CareType, list[str]] = {
    CareType.HOME_NURSING: [
        "wound_dressing", "injection_im", "catheter_care",
        "vitals_monitoring", "nebulization", "post_surgical_care",
        "elderly_care", "sample_collection",
    ],
    CareType.LAB_TEST_HOME: [
        "sample_collection", "home_phlebotomy",
    ],
    CareType.TELECONSULTATION: [
        "teleconsultation", "prescription", "report_review",
    ],
    CareType.PARAMEDIC_HOME_VISIT: [
        "vitals_monitoring", "injection_im", "wound_dressing",
        "nebulization", "elderly_care",
    ],
    CareType.EMERGENCY_112: [],
}
