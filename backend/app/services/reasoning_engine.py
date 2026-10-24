"""
CareCompass AI — Reasoning Engine Service (Stub)
Will be fully implemented in Phase 3/5.
"""

from __future__ import annotations


class ReasoningEngine:
    """
    Generates human-readable reasoning for triage decisions.
    Provides explainability for every recommendation.
    Stub for Phase 1 — full implementation in Phase 3/5.
    """

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
        Generate a human-readable reasoning string.
        Stub implementation — basic template-based reasoning.
        """
        if red_flags:
            flags_str = ", ".join(red_flags)
            return (
                f"Red-flag symptoms detected ({flags_str}); "
                f"routed to emergency services, not home care."
            )

        if is_follow_up:
            return "Input too vague to determine care type safely. Follow-up question asked."

        if care_type and urgency:
            return (
                f"Triage assessment: {care_type.replace('_', ' ')} "
                f"with {urgency.replace('_', ' ')} urgency. "
                f"Keywords: {', '.join(keywords) if keywords else 'none detected'}."
            )

        return "Assessment pending — insufficient information for classification."
