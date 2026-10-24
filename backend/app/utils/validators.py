"""
CareCompass AI — Input Validators
Security-focused validation for incoming requests.
"""

from __future__ import annotations

import re


# Common prompt injection patterns
_INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(previous|above|all)\s+instructions", re.IGNORECASE),
    re.compile(r"you\s+are\s+now", re.IGNORECASE),
    re.compile(r"system\s*prompt", re.IGNORECASE),
    re.compile(r"<\|.*?\|>", re.IGNORECASE),
    re.compile(r"\[\[.*?INST.*?\]\]", re.IGNORECASE),
    re.compile(r"forget\s+(everything|all)", re.IGNORECASE),
]


def is_prompt_injection(text: str) -> bool:
    """
    Detect common prompt injection attempts.

    Returns True if the text appears to contain injection patterns.
    """
    for pattern in _INJECTION_PATTERNS:
        if pattern.search(text):
            return True
    return False


def sanitize_input(text: str, max_length: int = 2000) -> str:
    """
    Sanitize user input for safe processing.

    - Strips HTML tags
    - Limits length
    - Removes control characters
    - Preserves Devanagari script
    """
    # Remove HTML tags
    text = re.sub(r"<[^>]+>", "", text)

    # Remove control characters (keep newlines and tabs)
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)

    # Limit length
    text = text[:max_length]

    # Normalize whitespace
    text = re.sub(r"\s+", " ", text).strip()

    return text


def validate_coordinates(lat: float, lng: float) -> bool:
    """
    Validate that coordinates are within the Delhi NCR region.
    Slightly expanded bounds for edge cases.
    """
    return 27.5 <= lat <= 29.5 and 76.0 <= lng <= 78.5
