"""
CareCompass AI — Follow-Up Engine Service
Determines information sufficiency and generates clinically targeted follow-up questions
to resolve ambiguity without making premature medical assumptions.
"""

from __future__ import annotations

import logging
import re
from typing import Optional

logger = logging.getLogger("carecompass.followup")


class FollowUpEngine:
    """
    Intelligent ambiguity detector and follow-up question generator.
    Trained on clinical triage best practices:
    - Never guess when symptoms or services are unstated.
    - Ask the ONE question that resolves ambiguity.
    """

    # Patterns indicating high ambiguity / insufficient information
    GREETING_PATTERNS = [
        re.compile(r"^(hi|hello|hey|namaste|नमस्ते|hola|good\s+(morning|afternoon|evening))\b", re.IGNORECASE),
        re.compile(r"^(hello\s+koi\s+hai|is\s+anyone\s+there|koi\s+hai\??)$", re.IGNORECASE),
        re.compile(r"^(नमस्ते,?\s*कोई\s*है\??)$", re.IGNORECASE),
    ]

    GENERIC_HELP_PATTERNS = [
        re.compile(r"^(i\s+need\s+help|help\s+me|help\s+chahiye|मदद\s*चाहिए|kuch\s+help\s+chahiye)$", re.IGNORECASE),
        re.compile(r"^(need\s+assistance|koi\s+madad\s+milegi)$", re.IGNORECASE),
    ]

    GENERIC_BOOKING_PATTERNS = [
        re.compile(r"^(i\s+want\s+to\s+book\s+something|mummy\s+ke\s+liye\s+kuch\s+book\s+karna\s+hai|माँ\s*के\s*लिए\s*कुछ\s*बुक\s*करना\s*है)", re.IGNORECASE),
        re.compile(r"^(book\s+karna\s+hai|appointment\s+chahiye)$", re.IGNORECASE),
    ]

    GENERIC_DOCTOR_PATTERNS = [
        re.compile(r"^(doctor\s+chahiye|डॉक्टर\s*चाहिए|need\s+a\s+doctor|want\s+a\s+doctor)$", re.IGNORECASE),
        re.compile(r"^(doctor\s+se\s+milna\s+hai|doctor\s+consult\s+chahiye)$", re.IGNORECASE),
    ]

    def is_ambiguous(
        self,
        text: str,
        keywords: list[str] | None = None,
        confidence: float = 1.0,
    ) -> tuple[bool, Optional[str]]:
        """
        Check if the request is too vague to assign a care type safely.

        Args:
            text: Normalized user input
            keywords: Extracted symptom/service keywords
            confidence: Classifier confidence score

        Returns:
            Tuple of (needs_follow_up, follow_up_question)
        """
        clean = text.strip()
        words = clean.split()

        # 1. Presence check / greeting
        for pat in self.GREETING_PATTERNS:
            if pat.search(clean):
                return True, (
                    "Happy to help. Could you tell me the main symptom or service you need "
                    "(home visit, nursing, lab test, or teleconsult)?"
                )

        # 2. Generic help
        for pat in self.GENERIC_HELP_PATTERNS:
            if pat.search(clean):
                return True, (
                    "Namaste! I'm here to help. Who is this for, and what's the concern — "
                    "fever, a nursing need, a lab test, or a doctor consult?"
                )

        # 3. Generic booking for family member without symptom/service
        for pat in self.GENERIC_BOOKING_PATTERNS:
            if pat.search(clean):
                return True, (
                    "Happy to help. Could you tell me the main symptom or service you need "
                    "(home visit, nursing, lab test, or teleconsult)?"
                )

        # 4. Generic doctor request without clinical details
        for pat in self.GENERIC_DOCTOR_PATTERNS:
            if pat.search(clean):
                return True, (
                    "Happy to help. Could you tell me the main symptom or service you need "
                    "(home visit, nursing, lab test, or teleconsult)?"
                )

        # 5. Low information density (extremely short input with no medical keywords)
        if len(words) <= 3 and (not keywords or len(keywords) == 0):
            return True, (
                "Could you tell me a little more about who this is for and what symptoms "
                "or care services you are looking for?"
            )

        # 6. Very low classifier confidence
        if confidence < 0.40 and (not keywords or len(keywords) == 0):
            return True, (
                "Could you clarify what kind of care is needed (such as a doctor video call, "
                "a home nurse visit, or home blood sample collection)?"
            )

        return False, None

    async def should_follow_up(
        self,
        text: str,
        keywords: list[str],
        confidence: float = 1.0,
    ) -> tuple[bool, str | None]:
        """Async interface for triage pipeline."""
        return self.is_ambiguous(text, keywords, confidence)
