"""
CareCompass AI — Triage Classifier Service (Stub)
Will be fully implemented in Phase 3.
"""

from __future__ import annotations

from app.models.schemas import TriageInternalResult


class TriageClassifier:
    """
    Hybrid triage classification using LLM + ML fallback.
    Stub for Phase 1 — returns placeholder results.
    Full implementation in Phase 3.
    """

    async def classify(
        self,
        text: str,
        detected_language: str,
        keywords: list[str],
        conversation_history: list | None = None,
    ) -> TriageInternalResult:
        """
        Classify the triage request into care_type + urgency.
        Stub implementation — Phase 3 will add LLM + ML classifier.
        """
        return TriageInternalResult(
            care_type=None,
            urgency=None,
            red_flags=[],
            reasoning="Triage classifier not yet implemented (Phase 3).",
            confidence=0.0,
            needs_follow_up=True,
            follow_up_question="Could you describe your symptoms in more detail?",
        )
