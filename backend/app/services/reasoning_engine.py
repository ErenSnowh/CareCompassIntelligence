"""
CareCompass AI — Clinical Reasoning Engine Service
Generates transparent, human-readable clinical justifications (Explainable AI - XAI).
Explains why a specific care type and urgency were recommended.
"""

from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger("carecompass.reasoning")


class ReasoningEngine:
    """
    Explainable AI (XAI) clinical justification engine.
    Produces clear chain-of-thought explanations for doctors, coordinators, and families.
    """

    CARE_TYPE_EXPLANATIONS = {
        "emergency_112": (
            "Critical red-flag symptoms detected ({flags}). Patient routed immediately to emergency 112 "
            "services, not home care."
        ),
        "paramedic_home_visit": (
            "Patient requires physical vitals check or in-person home health evaluation for acute symptoms "
            "without red flags. Sanocare Medic home visit recommended."
        ),
        "home_nursing": (
            "Prescribed clinical procedure (wound dressing, injection, catheter care, or post-surgical nursing) "
            "required at home. Assigned to qualified home nursing medic."
        ),
        "lab_test_home": (
            "Diagnostic blood test or pathology sample collection requested at home. Scheduled for "
            "home phlebotomist collection."
        ),
        "teleconsultation": (
            "Medical advice, report review, prescription renewal, or second opinion requested for stable symptoms. "
            "Appropriate for virtual teleconsultation with MBBS doctor."
        ),
    }

    def generate_reasoning(
        self,
        care_type: str | None,
        urgency: str | None,
        red_flags: list[str],
        detected_language: str,
        keywords: list[str],
        is_follow_up: bool = False,
    ) -> str:
        """
        Generate a human-readable clinical reasoning string.
        """
        # 1. Emergency Red Flags
        if red_flags:
            flags_str = ", ".join(flag.replace("_", " ") for flag in red_flags)
            return (
                f"Red-flag symptoms detected ({flags_str}); "
                f"routed to emergency services (112), not home care."
            )

        # 2. Ambiguity / Follow-Up
        if is_follow_up or care_type is None:
            return "Input too vague to determine care type safely. Follow-up question asked."

        # 3. Known Care Types
        base_explanation = self.CARE_TYPE_EXPLANATIONS.get(
            care_type,
            f"Assigned to {care_type.replace('_', ' ')} based on clinical symptom profile."
        )

        urgency_note = f"Urgency assessed as {urgency.replace('_', ' ')}." if urgency else ""

        if keywords:
            kw_str = ", ".join(keywords[:4])
            return f"{base_explanation} {urgency_note} Relevant symptoms/cues: {kw_str}."

        return f"{base_explanation} {urgency_note}"
