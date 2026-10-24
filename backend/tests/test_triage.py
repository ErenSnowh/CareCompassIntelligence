"""
Unit tests for CareCompass TriageClassifier and FollowUpEngine.
Validates classification accuracy across care types and multi-turn conversational progression.
"""

import pytest
from app.services.followup_engine import FollowUpEngine
from app.services.triage_classifier import TriageClassifier


@pytest.fixture
def classifier():
    return TriageClassifier()


@pytest.fixture
def followup_engine():
    return FollowUpEngine()


@pytest.mark.asyncio
async def test_followup_detection(followup_engine):
    # Greeting / presence
    needs_fu, q = await followup_engine.should_follow_up("Hi, is anyone there?", [])
    assert needs_fu is True
    assert q is not None

    # Generic help
    needs_fu, q = await followup_engine.should_follow_up("help chahiye", [])
    assert needs_fu is True
    assert "Namaste" in q or "help" in q

    # Generic doctor
    needs_fu, q = await followup_engine.should_follow_up("doctor chahiye", [])
    assert needs_fu is True
    assert q is not None

    # Clear symptom should NOT trigger follow-up
    needs_fu, q = await followup_engine.should_follow_up(
        "papa ko do din se bukhar hai aur khansi bhi", ["bukhar", "fever"]
    )
    assert needs_fu is False


@pytest.mark.asyncio
async def test_triage_care_types(classifier):
    # 1. Paramedic Home Visit
    res1 = await classifier.classify(
        text="papa ko do din se bukhar hai aur khansi bhi",
        detected_language="Hinglish",
        keywords=["bukhar", "khansi"],
    )
    assert res1.care_type == "paramedic_home_visit"
    assert res1.urgency == "same_day"
    assert res1.confidence > 0.5

    # 2. Home Nursing
    res2 = await classifier.classify(
        text="Grandmother has a bedsore that needs dressing",
        detected_language="English",
        keywords=["bedsore", "dressing"],
    )
    assert res2.care_type == "home_nursing"
    assert res2.urgency == "same_day"

    # 3. Lab Test Home
    res3 = await classifier.classify(
        text="Want a CBC and thyroid test with home sample collection",
        detected_language="English",
        keywords=["cbc", "thyroid", "sample"],
    )
    assert res3.care_type == "lab_test_home"
    assert res3.urgency == "scheduled"

    # 4. Teleconsultation
    res4 = await classifier.classify(
        text="Mild acidity and gas since morning, want to consult a doctor",
        detected_language="English",
        keywords=["acidity", "doctor", "consult"],
    )
    assert res4.care_type == "teleconsultation"
    assert res4.urgency == "same_day"

    # 5. Emergency 112
    res5 = await classifier.classify(
        text="My father is having severe chest pain and can't breathe",
        detected_language="English",
        keywords=["chest", "pain"],
    )
    assert res5.care_type == "emergency_112"
    assert res5.urgency == "emergency"
    assert res5.confidence == 1.0


@pytest.mark.asyncio
async def test_multi_turn_triage(classifier):
    # Turn 1: user says "doctor chahiye" -> system asks follow up
    res_turn1 = await classifier.classify(
        text="doctor chahiye",
        detected_language="Hinglish",
        keywords=[],
    )
    assert res_turn1.needs_follow_up is True
    assert res_turn1.care_type is None

    # Turn 2: user replies with symptoms in multi-turn conversation
    history = [
        {"role": "user", "text": "doctor chahiye"},
        {"role": "assistant", "follow_up_question": res_turn1.follow_up_question},
    ]

    res_turn2 = await classifier.classify(
        text="mummy ko 2 din se bukhar hai, ghar pe dikhana hai",
        detected_language="Hinglish",
        keywords=["bukhar"],
        conversation_history=history,
    )
    assert res_turn2.needs_follow_up is False
    assert res_turn2.care_type == "paramedic_home_visit"
    assert res_turn2.urgency == "same_day"
