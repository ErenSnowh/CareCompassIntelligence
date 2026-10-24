"""
CareCompass AI — Middleware: Audit Logger
Logs all triage requests and responses for traceability.
Implements zero-PII logging by hashing sensitive fields.
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger("carecompass.audit")


class AuditLogger:
    """
    Immutable audit logger for all triage decisions.
    Ensures every decision is traceable for medical-legal purposes.
    Implements zero-PII logging.
    """

    def __init__(self) -> None:
        self._entries: list[dict[str, Any]] = []

    def log_request(
        self,
        request_id: str,
        user_input_hash: str,
        location_hash: str,
        detected_language: str,
    ) -> None:
        """Log an incoming triage request (PII-safe)."""
        entry = {
            "event": "triage_request",
            "request_id": request_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "user_input_hash": user_input_hash,
            "location_hash": location_hash,
            "detected_language": detected_language,
        }
        self._entries.append(entry)
        logger.info("AUDIT | %s", json.dumps(entry))

    def log_response(
        self,
        request_id: str,
        care_type: str | None,
        urgency: str | None,
        red_flags: list[str],
        confidence: float,
        matched_count: int,
        latency_ms: float,
        is_follow_up: bool,
    ) -> None:
        """Log a triage response/decision."""
        entry = {
            "event": "triage_response",
            "request_id": request_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "care_type": care_type,
            "urgency": urgency,
            "red_flags": red_flags,
            "confidence": round(confidence, 3),
            "matched_caregivers_count": matched_count,
            "latency_ms": round(latency_ms, 1),
            "is_follow_up": is_follow_up,
        }
        self._entries.append(entry)
        logger.info("AUDIT | %s", json.dumps(entry))

    def log_emergency(self, request_id: str, red_flags: list[str]) -> None:
        """Log an emergency detection (highest priority)."""
        entry = {
            "event": "EMERGENCY_DETECTED",
            "request_id": request_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "red_flags": red_flags,
            "priority": "CRITICAL",
        }
        self._entries.append(entry)
        logger.critical("AUDIT | EMERGENCY | %s", json.dumps(entry))

    @staticmethod
    def generate_request_id() -> str:
        """Generate a unique request ID."""
        return f"REQ-{uuid.uuid4().hex[:12].upper()}"

    @staticmethod
    def hash_pii(value: str) -> str:
        """One-way hash for PII fields (input text, location)."""
        return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]

    @property
    def entries(self) -> list[dict[str, Any]]:
        """Get all audit entries (for admin dashboard)."""
        return self._entries.copy()

    def log_triage(
        self,
        user_input: str,
        response: Any,
        duration_ms: float,
    ) -> str:
        """Log a complete triage transaction with privacy-first hashing."""
        req_id = self.generate_request_id()
        hashed_input = self.hash_pii(user_input)

        if response.red_flags:
            self.log_emergency(req_id, response.red_flags)

        self.log_response(
            request_id=req_id,
            care_type=response.care_type,
            urgency=response.urgency,
            red_flags=response.red_flags,
            confidence=getattr(response, "confidence", 0.0),
            matched_count=len(response.matched_caregivers),
            latency_ms=duration_ms,
            is_follow_up=bool(response.follow_up_question),
        )
        return req_id

    def log_feedback(self, feedback_data: dict[str, Any]) -> None:
        """Log clinical coordinator feedback."""
        entry = {
            "event": "feedback_received",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **feedback_data,
        }
        self._entries.append(entry)
        logger.info("AUDIT | FEEDBACK | %s", json.dumps(entry))

    def get_summary(self) -> dict[str, Any]:
        """Alias for get_statistics for analytics summary."""
        return self.get_statistics()

    def get_statistics(self) -> dict[str, Any]:
        """Get audit statistics."""
        total = len(self._entries)
        emergencies = sum(
            1 for e in self._entries if e.get("event") == "EMERGENCY_DETECTED"
        )
        responses = [e for e in self._entries if e.get("event") == "triage_response"]
        avg_latency = (
            sum(e.get("latency_ms", 0) for e in responses) / len(responses)
            if responses
            else 0
        )

        return {
            "total_entries": total,
            "emergencies_detected": emergencies,
            "total_responses": len(responses),
            "average_latency_ms": round(avg_latency, 1),
        }

