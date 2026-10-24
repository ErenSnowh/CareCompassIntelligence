"""
CareCompass AI — FastAPI Main Application
Autonomous care triage and caregiver routing system for Indian healthcare.
"""

from __future__ import annotations

import logging
import time
from contextlib import asynccontextmanager
from typing import Any, Optional

from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.data.loader import DataLoader
from app.middleware.audit import AuditLogger
from app.middleware.security import SecurityMiddleware
from app.models.schemas import (
    CaregiverRecord,
    FeedbackRequest,
    MatchedCaregiver,
    TriageRequest,
    TriageResponse,
)
from app.services.caregiver_matcher import CaregiverMatcher
from app.services.followup_engine import FollowUpEngine
from app.services.language_processor import LanguageProcessor
from app.services.reasoning_engine import ReasoningEngine
from app.services.red_flag_detector import RedFlagDetector
from app.services.tinyfish_service import TinyFishService
from app.services.triage_classifier import TriageClassifier

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("carecompass.app")

settings = get_settings()

# Global state container for services
app_state: dict[str, Any] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize dataset loaders, ML pipelines, and API services on startup."""
    logger.info("Initializing CareCompass AI services...")

    # Data Loader
    data_loader = DataLoader(
        triage_path=settings.triage_dataset_path,
        caregivers_path=settings.caregivers_path,
    )
    data_loader.load()

    # Core Services
    language_processor = LanguageProcessor()
    red_flag_detector = RedFlagDetector()
    followup_engine = FollowUpEngine()
    triage_classifier = TriageClassifier()
    caregiver_matcher = CaregiverMatcher()
    reasoning_engine = ReasoningEngine()
    tinyfish_service = TinyFishService(api_key=settings.tinyfish_api_key)
    security_middleware = SecurityMiddleware()
    audit_logger = AuditLogger()

    app_state["data_loader"] = data_loader
    app_state["language_processor"] = language_processor
    app_state["red_flag_detector"] = red_flag_detector
    app_state["followup_engine"] = followup_engine
    app_state["triage_classifier"] = triage_classifier
    app_state["caregiver_matcher"] = caregiver_matcher
    app_state["reasoning_engine"] = reasoning_engine
    app_state["tinyfish_service"] = tinyfish_service
    app_state["security_middleware"] = security_middleware
    app_state["audit_logger"] = audit_logger

    logger.info("CareCompass AI services successfully initialized and ready for requests.")
    yield
    logger.info("Shutting down CareCompass AI...")
    app_state.clear()


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "CareCompass AI: Autonomous Clinical Care-Triage and Caregiver-Matching Engine. "
        "Delivers multilingual triage (Hindi/English/Hinglish), safety-first red flag detection, "
        "transparent clinical reasoning, and multi-signal caregiver allocation."
    ),
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled exception processing %s: %s", request.url.path, exc, exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "message": "An error occurred while processing the healthcare request.",
            "detail": str(exc) if settings.app_debug else None,
        },
    )


# --- API Routes ---

@app.get("/", tags=["General"])
async def root():
    """System entry point and service status."""
    return {
        "app": settings.app_name,
        "version": settings.app_version,
        "status": "online",
        "tagline": "From Symptoms to Safety — In Seconds, Not Hours.",
        "docs": "/docs",
    }


@app.get("/api/v1/health", tags=["Health & Observability"])
async def health_check():
    """Health check endpoint reporting system status and dataset statistics."""
    loader: DataLoader = app_state.get("data_loader")
    stats = loader.get_statistics() if loader else {}

    return {
        "status": "healthy",
        "app_name": settings.app_name,
        "version": settings.app_version,
        "environment": settings.app_env,
        "dataset_statistics": stats,
        "services": {
            "red_flag_detector": "active",
            "language_processor": "active",
            "triage_classifier": "active",
            "caregiver_matcher": "active",
            "tinyfish_service": "configured" if settings.tinyfish_api_key else "fallback_mode",
        },
    }


@app.post("/api/v1/triage", response_model=TriageResponse, tags=["Triage Core"])
async def process_triage(request: TriageRequest) -> TriageResponse:
    """
    Main Triage & Caregiver Routing Endpoint.

    Processes multilingual health requests:
    1. Input sanitization and security audit
    2. Language detection and normalization (EN/HI/Hinglish)
    3. Safety-First Red Flag Detection (Emergency 112 routing)
    4. Information sufficiency assessment (Follow-up questioning)
    5. Triage classification (care type, urgency, confidence scoring)
    6. Medical knowledge grounding (TinyFish integration)
    7. Multi-signal Caregiver Matching
    8. Explainable reasoning chain generation
    """
    start_time = time.time()
    security: SecurityMiddleware = app_state["security_middleware"]
    lang_proc: LanguageProcessor = app_state["language_processor"]
    rf_detector: RedFlagDetector = app_state["red_flag_detector"]
    fu_engine: FollowUpEngine = app_state["followup_engine"]
    classifier: TriageClassifier = app_state["triage_classifier"]
    matcher: CaregiverMatcher = app_state["caregiver_matcher"]
    reasoning_engine: ReasoningEngine = app_state["reasoning_engine"]
    tinyfish: TinyFishService = app_state["tinyfish_service"]
    loader: DataLoader = app_state["data_loader"]
    audit: AuditLogger = app_state["audit_logger"]

    # 1. Security & Sanitization
    sanitized_input = security.sanitize_input(request.user_input)

    # 2. Language Processing
    lang_info = lang_proc.process(
        text=sanitized_input,
        language_hint=request.language,
    )
    detected_lang = lang_info["detected_language"]
    normalized_text = lang_info["normalized_text"]
    keywords = lang_info["keywords"]

    # 3. SAFETY-FIRST: Red Flag Detection
    red_flags = rf_detector.detect(normalized_text)

    if red_flags:
        reasoning = reasoning_engine.generate_reasoning(
            care_type="emergency_112",
            urgency="emergency",
            red_flags=red_flags,
            detected_language=detected_lang,
            keywords=keywords,
            is_follow_up=False,
        )

        response = TriageResponse(
            follow_up_question=None,
            care_type="emergency_112",
            urgency="emergency",
            red_flags=red_flags,
            reasoning=reasoning,
            matched_caregivers=[],
            confidence=1.0,
            medical_context="CRITICAL EMERGENCY: Do not wait for home care. Call 112 or visit nearest emergency room immediately.",
        )

        audit.log_triage(
            user_input=request.user_input,
            response=response,
            duration_ms=(time.time() - start_time) * 1000,
        )
        return response

    # 4. Check for Information Sufficiency / Follow-up Needs
    needs_followup, followup_q = await fu_engine.should_follow_up(
        text=normalized_text,
        keywords=keywords,
        confidence=0.5,
    )

    if needs_followup and followup_q:
        reasoning = reasoning_engine.generate_reasoning(
            care_type=None,
            urgency=None,
            red_flags=[],
            detected_language=detected_lang,
            keywords=keywords,
            is_follow_up=True,
        )

        response = TriageResponse(
            follow_up_question=followup_q,
            care_type=None,
            urgency=None,
            red_flags=[],
            reasoning=reasoning,
            matched_caregivers=[],
            confidence=0.0,
            medical_context=None,
        )

        audit.log_triage(
            user_input=request.user_input,
            response=response,
            duration_ms=(time.time() - start_time) * 1000,
        )
        return response

    # 5. Triage Classification
    triage_result = await classifier.classify(
        text=normalized_text,
        detected_language=detected_lang,
        keywords=keywords,
        conversation_history=request.conversation_history,
    )

    # If classifier determined a follow-up is necessary
    if triage_result.needs_follow_up and triage_result.follow_up_question:
        response = TriageResponse(
            follow_up_question=triage_result.follow_up_question,
            care_type=None,
            urgency=None,
            red_flags=[],
            reasoning=triage_result.reasoning,
            matched_caregivers=[],
            confidence=0.0,
            medical_context=None,
        )
        audit.log_triage(
            user_input=request.user_input,
            response=response,
            duration_ms=(time.time() - start_time) * 1000,
        )
        return response

    # 6. TinyFish Medical Knowledge Grounding
    medical_ctx = await tinyfish.search_medical_context(
        symptoms=normalized_text
    )

    # 7. Caregiver Matching
    matched_caregivers = []
    if triage_result.care_type and triage_result.care_type != "emergency_112":
        matched_caregivers = matcher.match(
            care_type=triage_result.care_type,
            user_lat=request.location.lat,
            user_lng=request.location.lng,
            detected_language=detected_lang,
            caregivers=loader.active_caregivers,
            keywords=keywords,
            max_results=settings.max_matched_caregivers,
        )

    # 8. Reasoning Engine
    reasoning = reasoning_engine.generate_reasoning(
        care_type=triage_result.care_type,
        urgency=triage_result.urgency,
        red_flags=[],
        detected_language=detected_lang,
        keywords=keywords,
        is_follow_up=False,
    )

    response = TriageResponse(
        follow_up_question=None,
        care_type=triage_result.care_type,
        urgency=triage_result.urgency,
        red_flags=triage_result.red_flags,
        reasoning=reasoning,
        matched_caregivers=matched_caregivers,
        confidence=triage_result.confidence,
        medical_context=medical_ctx,
    )

    audit.log_triage(
        user_input=request.user_input,
        response=response,
        duration_ms=(time.time() - start_time) * 1000,
    )
    return response


@app.get("/api/v1/caregivers", response_model=list[CaregiverRecord], tags=["Caregiver Roster"])
async def list_caregivers(
    role: Optional[str] = None,
    language: Optional[str] = None,
    active_only: bool = True,
):
    """Retrieve caregiver directory with optional role, language, and status filtering."""
    loader: DataLoader = app_state.get("data_loader")
    if not loader:
        raise HTTPException(status_code=503, detail="Data loader not initialized")

    caregivers = loader.active_caregivers if active_only else loader.caregivers

    if role:
        caregivers = [cg for cg in caregivers if cg.role.lower() == role.lower()]

    if language:
        caregivers = [
            cg for cg in caregivers
            if any(language.lower() in lang.lower() for lang in cg.languages)
        ]

    return caregivers


@app.post("/api/v1/feedback", tags=["Continuous Learning"])
async def submit_feedback(feedback: FeedbackRequest):
    """
    Submit clinical coordinator feedback on triage decisions.
    Enables continuous model evaluation and few-shot tuning.
    """
    audit: AuditLogger = app_state["audit_logger"]
    audit.log_feedback(feedback.model_dump())
    return {
        "status": "success",
        "message": "Feedback recorded for continuous learning pipeline.",
        "request_id": feedback.request_id,
    }


@app.get("/api/v1/analytics/summary", tags=["Health & Observability"])
async def analytics_summary():
    """Retrieve real-time operational analytics and triage distribution summary."""
    loader: DataLoader = app_state.get("data_loader")
    audit: AuditLogger = app_state.get("audit_logger")

    dataset_stats = loader.get_statistics() if loader else {}
    audit_stats = audit.get_summary() if audit else {}

    return {
        "dataset_baseline": dataset_stats,
        "runtime_metrics": audit_stats,
    }
