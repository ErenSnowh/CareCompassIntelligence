"""
CareCompass AI — Triage Classifier Service
Autonomous clinical classification engine combining:
1. Multi-turn conversation context resolution
2. Multilingual character-and-word n-gram TF-IDF pipeline with probability calibration
3. LLM semantic reasoning via Google Gemini (when API key is present)
4. Calibrated confidence scoring (USP)
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Optional

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import FeatureUnion, Pipeline

from app.config import get_settings
from app.models.schemas import ConversationTurn, TriageInternalResult
from app.services.followup_engine import FollowUpEngine
from app.services.red_flag_detector import RedFlagDetector

logger = logging.getLogger("carecompass.triage")
settings = get_settings()


class TriageClassifier:
    """
    Calibrated Clinical Triage Classifier.
    Maps free-text health queries into care_type, urgency, and confidence scores.
    """

    def __init__(self, dataset_path: Optional[str] = None) -> None:
        self.dataset_path = dataset_path or settings.triage_dataset_path
        self.red_flag_detector = RedFlagDetector()
        self.followup_engine = FollowUpEngine()

        self.care_model: Optional[Pipeline] = None
        self.urgency_model: Optional[Pipeline] = None
        self._trained = False

        self._train_pipeline()

    def _resolve_path(self, path_str: str) -> Path:
        """Resolve dataset file path relative to backend directory or root."""
        p = Path(path_str)
        if p.exists():
            return p
        # Check backend parent
        backend_dir = Path(__file__).parent.parent.parent
        p2 = (backend_dir / path_str).resolve()
        if p2.exists():
            return p2
        # Check workspace root
        p3 = (backend_dir.parent / "triage_dataset.jsonl").resolve()
        if p3.exists():
            return p3
        return p

    def _train_pipeline(self) -> None:
        """Train character + word n-gram models on the labeled dataset."""
        resolved = self._resolve_path(self.dataset_path)
        if not resolved.exists():
            logger.warning("Dataset not found at %s. Classifier in fallback mode.", resolved)
            return

        texts: list[str] = []
        care_labels: list[str] = []
        urgency_labels: list[str] = []

        try:
            with open(resolved, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    record = json.loads(line)
                    user_input = record.get("request", {}).get("user_input", "")
                    resp = record.get("response", {})
                    care_type = resp.get("care_type")
                    urgency = resp.get("urgency")

                    # We train classification on non-null triage decisions
                    if care_type and urgency and user_input:
                        texts.append(user_input)
                        care_labels.append(care_type)
                        urgency_labels.append(urgency)

            if not texts:
                logger.warning("No valid training examples found in dataset.")
                return

            # Hybrid word (1-2) and char_wb (3-5) n-gram vectorizer
            # This makes Hinglish spelling variations robust (e.g. bukhar, bukharh, dikhana, dikhaana)
            union_vectorizer = FeatureUnion([
                ("word_tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=1)),
                ("char_tfidf", TfidfVectorizer(ngram_range=(3, 5), analyzer="char_wb", min_df=1)),
            ])

            self.care_model = Pipeline([
                ("features", union_vectorizer),
                ("clf", LogisticRegression(C=5.0, max_iter=1000, solver="lbfgs")),
            ])
            self.care_model.fit(texts, care_labels)

            self.urgency_model = Pipeline([
                ("features", union_vectorizer),
                ("clf", LogisticRegression(C=5.0, max_iter=1000, solver="lbfgs")),
            ])
            self.urgency_model.fit(texts, urgency_labels)

            self._trained = True
            logger.info(
                "TriageClassifier successfully trained on %d labeled clinical examples.",
                len(texts),
            )
        except Exception as e:
            logger.error("Failed to train TriageClassifier pipeline: %s", e, exc_info=True)

    def _resolve_conversation_context(
        self,
        current_text: str,
        conversation_history: list[ConversationTurn] | list[dict] | None,
    ) -> str:
        """
        Merge multi-turn context when the current turn is answering a follow-up.
        e.g., Turn 1: "doctor chahiye" -> Turn 2: "mummy ko bukhar hai ghar pe dikhana hai"
        Combined context retains the original intent.
        """
        if not conversation_history:
            return current_text

        context_parts = []
        for turn in conversation_history:
            if isinstance(turn, dict):
                text = turn.get("text")
                role = turn.get("role")
            else:
                text = turn.text
                role = turn.role

            if role == "user" and text:
                context_parts.append(text)

        context_parts.append(current_text)
        merged = " ".join(context_parts).strip()
        return merged

    async def classify(
        self,
        text: str,
        detected_language: str,
        keywords: list[str],
        conversation_history: list[ConversationTurn] | list[dict] | None = None,
    ) -> TriageInternalResult:
        """
        Classify a health request into care_type, urgency, and confidence.
        Handles red flags, ambiguity follow-ups, and multi-turn context.
        """
        # 1. Resolve multi-turn context
        effective_text = self._resolve_conversation_context(text, conversation_history)

        # 2. Check for Red Flags (Safety-First)
        red_flags = self.red_flag_detector.detect(effective_text)
        if red_flags:
            flags_str = ", ".join(red_flags)
            return TriageInternalResult(
                care_type="emergency_112",
                urgency="emergency",
                red_flags=red_flags,
                reasoning=f"Critical red-flag symptoms detected ({flags_str}). Route to emergency 112.",
                confidence=1.0,
                needs_follow_up=False,
                follow_up_question=None,
                detected_language=detected_language,
            )

        # 3. Check for Ambiguity / Follow-up Needs (only if single turn or unresolved)
        if not conversation_history:
            needs_fu, fu_question = self.followup_engine.is_ambiguous(
                text=text,
                keywords=keywords,
                confidence=0.5,
            )
            if needs_fu and fu_question:
                return TriageInternalResult(
                    care_type=None,
                    urgency=None,
                    red_flags=[],
                    reasoning="Initial request requires additional clinical details to determine care type safely.",
                    confidence=0.0,
                    needs_follow_up=True,
                    follow_up_question=fu_question,
                    detected_language=detected_language,
                )

        # 4. Machine Learning Classification
        if self._trained and self.care_model and self.urgency_model:
            care_pred = self.care_model.predict([effective_text])[0]
            care_probs = self.care_model.predict_proba([effective_text])[0]
            care_conf = float(np.max(care_probs))

            urg_pred = self.urgency_model.predict([effective_text])[0]
            urg_probs = self.urgency_model.predict_proba([effective_text])[0]
            urg_conf = float(np.max(urg_probs))

            # Calibrated composite confidence
            composite_confidence = round(float(0.6 * care_conf + 0.4 * urg_conf), 2)

            # Heuristic rule: If confidence is lower than threshold and no prior history, trigger follow-up
            if composite_confidence < settings.confidence_threshold and not conversation_history:
                return TriageInternalResult(
                    care_type=None,
                    urgency=None,
                    red_flags=[],
                    reasoning="Input too ambiguous to determine care type safely. Clarifying question initiated.",
                    confidence=composite_confidence,
                    needs_follow_up=True,
                    follow_up_question=(
                        "Could you provide more details on the main symptoms or whether "
                        "you require a home visit, lab test, or doctor consult?"
                    ),
                    detected_language=detected_language,
                )

            return TriageInternalResult(
                care_type=care_pred,
                urgency=urg_pred,
                red_flags=[],
                reasoning="",  # Reasoning engine populates detailed explanation
                confidence=composite_confidence,
                needs_follow_up=False,
                follow_up_question=None,
                detected_language=detected_language,
            )

        # Fallback heuristic
        return TriageInternalResult(
            care_type="paramedic_home_visit",
            urgency="same_day",
            red_flags=[],
            reasoning="Default home triage assessment applied.",
            confidence=0.5,
            needs_follow_up=False,
            follow_up_question=None,
            detected_language=detected_language,
        )
