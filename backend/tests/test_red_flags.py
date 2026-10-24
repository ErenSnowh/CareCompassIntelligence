"""
Comprehensive unit and safety tests for CareCompass Red Flag Detector.
Validates 100% emergency recall across all 9 controlled red flag categories in EN/HI/Hinglish.
"""

import json
from pathlib import Path
import pytest
from app.services.red_flag_detector import RedFlagDetector


@pytest.fixture
def detector():
    return RedFlagDetector()


def test_chest_pain_multilingual(detector):
    assert "chest_pain" in detector.detect("My father is having severe chest pain")
    assert "chest_pain" in detector.detect("papa ko kal seene me dard ho raha hai")
    assert "chest_pain" in detector.detect("मरीज के सीने में दर्द है")


def test_breathlessness_multilingual(detector):
    assert "breathlessness" in detector.detect("Patient cannot breathe properly and gasping")
    assert "breathlessness" in detector.detect("saans nahi aa rahi hai bahut dikkat hai")
    assert "breathlessness" in detector.detect("मरीज को सांस लेने में तकलीफ हो रही है")


def test_unconsciousness_multilingual(detector):
    assert "unconsciousness" in detector.detect("He suddenly collapsed and is not responding")
    assert "unconsciousness" in detector.detect("wo achanak gir gaye response nahi de rahe")
    assert "unconsciousness" in detector.detect("मरीज बेहोश हो गया है")


def test_severe_bleeding_multilingual(detector):
    assert "severe_bleeding" in detector.detect("Heavy bleeding that won't stop after an accident")
    assert "severe_bleeding" in detector.detect("accident ke baad bleeding ruk nahi rahi")
    assert "severe_bleeding" in detector.detect("एक्सीडेंट के बाद खून नहीं रुक रहा")


def test_stroke_symptoms(detector):
    assert "stroke_symptoms" in detector.detect("Patient has face drooping and slurred speech")
    assert "stroke_symptoms" in detector.detect("face ek taraf tedha ho gaya aur zubaan ladkhada rahi hai")
    assert "stroke_symptoms" in detector.detect("चेहरा टेढ़ा हो गया है और आवाज लड़खड़ा रही है")


def test_seizure(detector):
    assert "seizure" in detector.detect("Patient is having continuous seizure and fits")
    assert "seizure" in detector.detect("mirgi ka daura pad gaya body akad gayi")
    assert "seizure" in detector.detect("बच्चे को मिर्गी का दौरा आ रहा है")


def test_high_fever_infant(detector):
    assert "high_fever_infant" in detector.detect("Newborn infant high fever 104 burning hot")
    assert "high_fever_infant" in detector.detect("chote baby ko bahut tez bukhar hai")
    assert "high_fever_infant" in detector.detect("नवजात शिशु को तेज बुखार है")


def test_suicidal_ideation(detector):
    assert "suicidal_ideation" in detector.detect("Patient stated they want to die and kill myself")
    assert "suicidal_ideation" in detector.detect("mujhe suicide karna hai zindagi khatam karni hai")
    assert "suicidal_ideation" in detector.detect("वह आत्महत्या करना चाहता है")


def test_severe_dehydration(detector):
    assert "severe_dehydration" in detector.detect("Severe dehydration with sunken eyes and no urine")
    assert "severe_dehydration" in detector.detect("severe dehydration ho gaya peshab nahi aa raha 24 ghante se")
    assert "severe_dehydration" in detector.detect("पानी की अत्यधिक कमी और आंखें धंस गई हैं")


def test_negation_awareness(detector):
    # Negations should not trigger red flag alarms
    assert len(detector.detect("Mild fever for 2 days, no chest pain")) == 0
    assert len(detector.detect("Normal headache, without breathlessness")) == 0
    assert len(detector.detect("halka bukhar hai seene me dard nahi hai")) == 0


def test_dataset_emergency_recall(detector):
    dataset_path = Path("triage_dataset.jsonl")
    if not dataset_path.exists():
        pytest.skip("Dataset file not found at project root")

    with open(dataset_path, "r", encoding="utf-8") as f:
        records = [json.loads(line) for line in f if line.strip()]

    emergencies = [
        r for r in records
        if r.get("response", {}).get("care_type") == "emergency_112"
    ]
    non_emergencies = [
        r for r in records
        if r.get("response", {}).get("care_type") != "emergency_112"
    ]

    # Evaluate Recall
    missed = [
        r["request"]["user_input"]
        for r in emergencies
        if not detector.detect(r["request"]["user_input"])
    ]
    assert len(missed) == 0, f"Missed emergencies: {missed}"

    # Evaluate Precision
    false_positives = [
        r["request"]["user_input"]
        for r in non_emergencies
        if detector.detect(r["request"]["user_input"])
    ]
    assert len(false_positives) == 0, f"False positives on non-emergencies: {false_positives}"


def test_emergency_guidance_generation(detector):
    guidance = detector.get_emergency_guidance(["chest_pain", "breathlessness"])
    assert "112" in guidance
    assert "upright" in guidance.lower() or "chest" in guidance.lower()
