"""Supabase integration service for CareCompass AI.

Provides a thin, safe wrapper around the Supabase Python client. The service
is optional: if SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY are not configured,
it degrades gracefully (fallback_mode) so local development and tests keep
working without a live database.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

logger = logging.getLogger("carecompass.supabase")

try:
    from supabase import create_client, Client  # type: ignore

    SUPABASE_AVAILABLE = True
except Exception:  # pragma: no cover - import guard
    create_client = None  # type: ignore
    Client = Any  # type: ignore
    SUPABASE_AVAILABLE = False


class SupabaseService:
    """Wrapper around the Supabase client."""

    def __init__(
        self,
        url: Optional[str] = None,
        anon_key: Optional[str] = None,
        service_role_key: Optional[str] = None,
    ) -> None:
        self.url = (url or "").strip() or None
        self.anon_key = (anon_key or "").strip() or None
        self.service_role_key = (service_role_key or "").strip() or None
        self._client: Optional[Any] = None
        self._error: Optional[str] = None

        if not SUPABASE_AVAILABLE:
            self._error = "supabase package not installed"
            return

        if not self.url or not (self.service_role_key or self.anon_key):
            self._error = "supabase credentials not configured"
            return

        key = self.service_role_key or self.anon_key
        try:
            self._client = create_client(self.url, key)
            logger.info("Supabase client initialized (url=%s)", self.url)
        except Exception as exc:  # pragma: no cover - network/runtime
            self._error = str(exc)
            self._client = None
            logger.warning("Supabase client init failed: %s", exc)

    # ------------------------------------------------------------------ #
    # Status
    # ------------------------------------------------------------------ #
    @property
    def is_configured(self) -> bool:
        return self._client is not None

    @property
    def mode(self) -> str:
        return "configured" if self.is_configured else "fallback_mode"

    @property
    def error(self) -> Optional[str]:
        return self._error

    @property
    def client(self) -> Optional[Any]:
        return self._client

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    def health(self) -> dict[str, Any]:
        """Lightweight connectivity probe."""
        if not self.is_configured:
            return {"status": "fallback_mode", "error": self._error}
        try:
            # A cheap round-trip against the REST endpoint.
            self._client.table("health").select("id").limit(1).execute()
            return {"status": "healthy"}
        except Exception as exc:
            # Table may not exist yet; connection itself is still OK.
            return {"status": "connected", "note": str(exc)}

    def insert_triage_log(self, payload: dict[str, Any]) -> Optional[dict[str, Any]]:
        """Best-effort insert into `triage_logs` table. Never raises."""
        if not self.is_configured:
            return None
        try:
            res = self._client.table("triage_logs").insert(payload).execute()
            return getattr(res, "data", None)
        except Exception as exc:
            logger.warning("Supabase insert_triage_log failed: %s", exc)
            return None