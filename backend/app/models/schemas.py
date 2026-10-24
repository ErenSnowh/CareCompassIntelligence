"""
CareCompass AI — Pydantic Schemas
Request/Response models for the triage API.
Extends the base contract with confidence scoring and medical context (USPs).
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


# --- Request Models ---

class Location(BaseModel):
    """Geographic coordinates (Delhi NCR region)."""
    lat: float = Field(..., ge=27.5, le=29.5, description="Latitude")
    lng: float = Field(..., ge=76.0, le=78.5, description="Longitude")


class ConversationTurn(BaseModel):
    """A single turn in the conversation history."""
    role: str = Field(..., pattern="^(user|assistant)$")
    text: Optional[str] = None
    follow_up_question: Optional[str] = None
    care_type: Optional[str] = None
    urgency: Optional[str] = None
    red_flags: list[str] = []
    reasoning: Optional[str] = None


class TriageRequest(BaseModel):
    """
    Incoming triage request from user/WhatsApp.
    Matches the exact API contract from the problem statement.
    """
    user_input: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Free-text health request (EN/HI/Hinglish)",
    )
    language: str = Field(
        default="auto",
        description="Language hint; 'auto' for automatic detection",
    )
    location: Location = Field(
        ...,
        description="User's geographic location",
    )
    conversation_history: list[ConversationTurn] = Field(
        default_factory=list,
        description="Previous turns in the conversation",
    )


# --- Response Models ---

class MatchedCaregiver(BaseModel):
    """A caregiver matched to the request, with score and reasoning."""
    caregiver_id: str = Field(..., description="Unique caregiver ID (e.g., CG_014)")
    score: float = Field(..., ge=0.0, le=1.0, description="Match score (0-1)")
    reason: str = Field(..., description="Human-readable match reasoning")


class TriageResponse(BaseModel):
    """
    Triage response — either a decision or a follow-up question.
    Extends the base contract with confidence and medical_context (USP fields).
    """
    # --- Core Contract Fields ---
    follow_up_question: Optional[str] = Field(
        default=None,
        description="Non-null ONLY when more info is needed",
    )
    care_type: Optional[str] = Field(
        default=None,
        description="Recommended care type (null if follow-up needed)",
    )
    urgency: Optional[str] = Field(
        default=None,
        description="Urgency level (null if follow-up needed)",
    )
    red_flags: list[str] = Field(
        default_factory=list,
        description="Detected red flags (non-empty → emergency)",
    )
    reasoning: str = Field(
        ...,
        description="Human-readable justification for the decision",
    )
    matched_caregivers: list[MatchedCaregiver] = Field(
        default_factory=list,
        description="Top 1-3 matched caregivers",
    )

    # --- USP Extension Fields ---
    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Model confidence in the triage decision (0-1)",
    )
    detected_language: Optional[str] = Field(
        default=None,
        description="Detected language of the input",
    )
    medical_context: Optional[str] = Field(
        default=None,
        description="Medical context from TinyFish knowledge grounding",
    )


# --- Internal Models (not exposed via API) ---

class CaregiverRecord(BaseModel):
    """Internal representation of a caregiver from caregivers.csv."""
    caregiver_id: str
    name: str
    role: str
    qualification: str
    gender: str
    languages: list[str]
    skills: list[str]
    base_area: str
    base_lat: float
    base_lng: float
    max_radius_km: float
    tier: Optional[str] = None
    rating: float
    experience_years: int
    free_from: str
    free_until: str
    active: bool


class TriageInternalResult(BaseModel):
    """Internal result from the triage classifier (before caregiver matching)."""
    care_type: Optional[str] = None
    urgency: Optional[str] = None
    red_flags: list[str] = []
    reasoning: str = ""
    confidence: float = 0.0
    follow_up_question: Optional[str] = None
    detected_language: Optional[str] = None
    needs_follow_up: bool = False


# --- Feedback Model ---

class FeedbackRequest(BaseModel):
    """User/admin feedback on a triage decision."""
    request_id: str = Field(..., description="ID of the original request")
    correct_care_type: Optional[str] = None
    correct_urgency: Optional[str] = None
    was_helpful: bool = True
    notes: Optional[str] = None
