"""
CareCompass AI — Caregiver Matcher Service (Stub)
Will be fully implemented in Phase 4.
"""

from __future__ import annotations

from app.models.schemas import CaregiverRecord, MatchedCaregiver


class CaregiverMatcher:
    """
    Multi-signal caregiver matching engine.
    Stub for Phase 1 — full implementation in Phase 4.
    """

    def match(
        self,
        care_type: str,
        user_lat: float,
        user_lng: float,
        detected_language: str,
        caregivers: list[CaregiverRecord],
        keywords: list[str] | None = None,
        max_results: int = 3,
    ) -> list[MatchedCaregiver]:
        """
        Match and rank caregivers for a triage decision.
        Stub implementation — Phase 4 will add full scoring.
        """
        return []
