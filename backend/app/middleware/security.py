"""
CareCompass AI — Middleware: Security
Rate limiting, input sanitization, and security headers.
"""

from __future__ import annotations

import time
import logging
from collections import defaultdict
from typing import Any

from fastapi import HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.utils.validators import is_prompt_injection, sanitize_input

logger = logging.getLogger("carecompass.security")


class RateLimiter:
    """Simple in-memory rate limiter (per IP)."""

    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: dict[str, list[float]] = defaultdict(list)

    def is_allowed(self, client_ip: str) -> bool:
        """Check if the client IP is within rate limits."""
        now = time.time()
        # Clean old entries
        self._requests[client_ip] = [
            ts
            for ts in self._requests[client_ip]
            if now - ts < self.window_seconds
        ]
        # Check limit
        if len(self._requests[client_ip]) >= self.max_requests:
            return False
        self._requests[client_ip].append(now)
        return True

    def get_remaining(self, client_ip: str) -> int:
        """Get remaining requests for the current window."""
        now = time.time()
        active = [
            ts
            for ts in self._requests.get(client_ip, [])
            if now - ts < self.window_seconds
        ]
        return max(0, self.max_requests - len(active))


class SecurityMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for security:
    - Rate limiting
    - Security headers
    - Request logging
    """

    def __init__(self, app: Any = None, rate_limiter: RateLimiter | None = None):
        if app is not None:
            super().__init__(app)
        self.rate_limiter = rate_limiter or RateLimiter()

    @staticmethod
    def sanitize_input(text: str) -> str:
        """Sanitize text and guard against prompt injection."""
        if is_prompt_injection(text):
            logger.warning("Potential prompt injection pattern detected in input")
        return sanitize_input(text)


    async def dispatch(self, request: Request, call_next: Any) -> Response:
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"

        # Rate limiting
        if not self.rate_limiter.is_allowed(client_ip):
            logger.warning("Rate limit exceeded for %s", client_ip)
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded. Please try again later.",
            )

        # Process request
        response = await call_next(request)

        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Request-ID"] = request.state.request_id if hasattr(request.state, "request_id") else ""

        # Add rate limit headers
        remaining = self.rate_limiter.get_remaining(client_ip)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Limit"] = str(
            self.rate_limiter.max_requests
        )

        return response
