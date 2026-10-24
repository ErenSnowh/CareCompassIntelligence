"""
CareCompass AI — Follow-Up Engine Service (Stub)
Will be fully implemented in Phase 3.
"""

from __future__ import annotations


class FollowUpEngine:
    """
    Determines when to ask a follow-up question vs. commit to a triage decision.
    Stub for Phase 1 — full implementation in Phase 3.
    """

    async def should_follow_up(
        self, text: str, keywords: list[str], confidence: float
    ) -> tuple[bool, str | None]:
        """
        Decide if a follow-up question is needed.

        Returns:
            Tuple of (needs_follow_up, follow_up_question_or_none)
        """
        # Phase 1: Simple heuristic — if too few keywords, ask
        if len(keywords) < 1 and len(text.split()) < 4:
            return True, (
                "Could you tell me more about the symptoms? "
                "For example, is there fever, pain, bleeding, or breathing difficulty?"
            )
        return False, None
