"""
CareCompass AI — Red Flag Detector Service (Stub)
Will be fully implemented in Phase 2.
Provides a basic keyword-based Layer 1 scanner in Phase 1.
"""

from __future__ import annotations

import re
import logging
from typing import Optional

logger = logging.getLogger("carecompass.safety")


class RedFlagDetector:
    """
    Dual-layer red flag detection system.

    Layer 1 (Phase 1): Rule-based keyword matching (deterministic, instant)
    Layer 2 (Phase 2): LLM semantic analysis (contextual, catches implicit emergencies)

    Design principle: High recall > High precision.
    If EITHER layer detects a red flag → EMERGENCY.
    """

    # Multilingual red flag keyword dictionary
    RED_FLAG_KEYWORDS: dict[str, list[str]] = {
        "chest_pain": [
            "chest pain", "chest tight", "heart attack", "crushing chest",
            "seene mein dard", "chhati mein dard", "dil ka daura",
            "chest pain ho raha", "seene me pain", "heart attack",
            "seene mein jalan", "dil mein dard",
        ],
        "breathlessness": [
            "can't breathe", "cannot breathe", "difficulty breathing",
            "shortness of breath", "gasping", "choking",
            "saans nahi aa rahi", "saans lene mein takleef", "dum ghut raha",
            "breathing problem", "saans nahi", "breathless",
            "saans phool", "dam ghutna",
        ],
        "unconsciousness": [
            "unconscious", "passed out", "fainted", "not responding",
            "collapsed", "unresponsive", "coma",
            "behosh", "hosh nahi", "gir gaya", "jawab nahi de raha",
            "behosh ho gaya", "respond nahi kar raha",
        ],
        "severe_bleeding": [
            "heavy bleeding", "bleeding won't stop", "blood loss",
            "hemorrhage", "profuse bleeding", "bleeding heavily",
            "khoon band nahi ho raha", "bahut khoon", "khoon beh raha",
            "bleeding ruk nahi rahi", "bahut blood aa raha",
        ],
        "stroke_symptoms": [
            "face drooping", "slurred speech", "arm weakness", "stroke",
            "one side numb", "paralysis", "lakwa",
            "chehra tedha", "bolne mein dikkat", "haath mein kamzori",
            "face ek taraf", "speech slur", "ek taraf kamzori",
        ],
        "seizure": [
            "seizure", "convulsion", "fits", "jerking", "epilepsy attack",
            "mirgi ka daura", "jhatkhe aa rahe", "body akad gayi",
            "seizure aa raha", "fits aa rahe", "mirgi attack",
        ],
        "high_fever_infant": [
            "baby high fever", "infant fever", "newborn temperature",
            "baby fever", "toddler high fever", "child very hot",
            "bachche ko tez bukhar", "shishu ko bukhar",
            "baby ko high fever", "bachche ka temperature",
            "neonatal fever", "infant hot",
        ],
        "suicidal_ideation": [
            "want to die", "kill myself", "end my life", "suicidal",
            "suicide", "don't want to live", "no reason to live",
            "marna chahta", "jaan dena chahta", "zindagi khatam",
            "suicide karna hai", "life end karna hai",
            "marna hai mujhe", "jeene ka man nahi",
        ],
        "severe_dehydration": [
            "severe dehydration", "not urinating", "sunken eyes",
            "very dry mouth", "no tears", "extremely thirsty",
            "paani ki kami", "peshab nahi aa raha", "aankhein dhans gayi",
            "dehydration ho gaya", "pani nahi pi pa raha",
        ],
    }

    def detect(self, text: str) -> list[str]:
        """
        Layer 1: Rule-based red flag detection.
        Scans text against multilingual keyword dictionary.

        Args:
            text: Normalized user input text

        Returns:
            List of detected red flag codes (empty if safe)
        """
        text_lower = text.lower()
        detected_flags: list[str] = []

        for flag_code, keywords in self.RED_FLAG_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text_lower:
                    if flag_code not in detected_flags:
                        detected_flags.append(flag_code)
                        logger.warning(
                            "RED FLAG DETECTED: %s (matched: '%s')",
                            flag_code,
                            keyword,
                        )
                    break  # One match is enough for this flag

        return detected_flags

    def is_emergency(self, text: str) -> tuple[bool, list[str]]:
        """
        Check if the input triggers an emergency response.

        Returns:
            Tuple of (is_emergency, list_of_red_flags)
        """
        flags = self.detect(text)
        return len(flags) > 0, flags
