"""
CareCompass AI — TinyFish Integration Service (Stub)
Will be fully implemented in Phase 5.
"""

from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger("carecompass.tinyfish")


class TinyFishService:
    """
    Integrates TinyFish APIs for medical knowledge grounding.
    - Search API (FREE): Medical context validation
    - Fetch API (FREE): Clinical guideline extraction
    - Agent API ($0.016/step): Caregiver credential verification

    Stub for Phase 1 — full implementation in Phase 5.
    """

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key
        self._available = api_key is not None

    async def search_medical_context(self, symptoms: str) -> Optional[str]:
        """Search for relevant medical guidelines (FREE API)."""
        if not self._available:
            logger.debug("TinyFish not configured — skipping medical context search")
            return None
        # Phase 5 implementation
        return None

    async def fetch_care_guidelines(self, condition_url: str) -> Optional[str]:
        """Fetch and clean medical guideline content (FREE API)."""
        if not self._available:
            return None
        # Phase 5 implementation
        return None

    async def verify_caregiver_credentials(
        self, registration_number: str
    ) -> Optional[dict]:
        """Verify caregiver registration (Agent API — paid)."""
        if not self._available:
            return None
        # Phase 5 implementation
        return None
