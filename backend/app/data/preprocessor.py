"""
CareCompass AI — Text Preprocessor
Normalizes, cleans, and prepares text for the NLU pipeline.
Handles Hindi, English, and Hinglish inputs.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Optional


class TextPreprocessor:
    """Cleans and normalizes multilingual health request text."""

    # Common Hinglish/Hindi abbreviations and their expansions
    EXPANSIONS = {
        "bp": "blood pressure",
        "ecg": "electrocardiogram",
        "iv": "intravenous",
        "im": "intramuscular",
        "opd": "outpatient department",
        "icu": "intensive care unit",
        "cbc": "complete blood count",
        "rbs": "random blood sugar",
        "hba1c": "glycated hemoglobin",
        "dr": "doctor",
        "doc": "doctor",
    }

    # Transliteration map for common Hinglish patterns
    HINGLISH_NORMALIZATIONS = {
        "bukhar": "fever",
        "khansi": "cough",
        "sardee": "cold",
        "sardi": "cold",
        "dard": "pain",
        "seene": "chest",
        "chhati": "chest",
        "sir": "head",
        "pet": "stomach",
        "ulti": "vomiting",
        "dast": "diarrhea",
        "behosh": "unconscious",
        "khoon": "blood",
        "saans": "breathing",
        "chakkar": "dizziness",
        "kamzori": "weakness",
        "sujan": "swelling",
        "ghav": "wound",
        "injection": "injection",
        "dawai": "medicine",
        "tablet": "tablet",
        "patti": "bandage",
        "nasha": "intoxication",
    }

    def normalize(self, text: str) -> str:
        """
        Full normalization pipeline for incoming user text.

        Steps:
        1. Unicode normalization (NFC)
        2. Lowercase
        3. Remove excessive whitespace
        4. Strip punctuation (keep essential)
        5. Expand medical abbreviations
        """
        if not text:
            return ""

        # Unicode normalize
        text = unicodedata.normalize("NFC", text)

        # Lowercase
        text = text.lower().strip()

        # Remove excessive whitespace
        text = re.sub(r"\s+", " ", text)

        # Remove special characters but keep Devanagari, Latin, digits, and basic punctuation
        text = re.sub(r"[^\w\s\u0900-\u097F.,!?;:\-']", " ", text)

        # Expand medical abbreviations
        words = text.split()
        expanded = []
        for word in words:
            clean_word = word.strip(".,!?;:")
            if clean_word in self.EXPANSIONS:
                expanded.append(self.EXPANSIONS[clean_word])
            else:
                expanded.append(word)

        return " ".join(expanded)

    def detect_language(self, text: str) -> str:
        """
        Simple language detection based on script analysis.

        Returns: "English", "Hindi", or "Hinglish"
        """
        if not text:
            return "English"

        # Count Devanagari characters
        devanagari_count = sum(
            1 for char in text if "\u0900" <= char <= "\u097F"
        )
        # Count Latin characters
        latin_count = sum(1 for char in text if char.isascii() and char.isalpha())

        total = devanagari_count + latin_count
        if total == 0:
            return "English"

        devanagari_ratio = devanagari_count / total

        if devanagari_ratio > 0.7:
            return "Hindi"
        elif devanagari_ratio < 0.1:
            # Check for Hinglish patterns (Hindi words in Latin script)
            hinglish_words = sum(
                1 for word in text.lower().split()
                if word.strip(".,!?;:") in self.HINGLISH_NORMALIZATIONS
                or word.strip(".,!?;:") in self._hinglish_markers()
            )
            if hinglish_words >= 1:
                return "Hinglish"
            return "English"
        else:
            return "Hinglish"

    def extract_keywords(self, text: str) -> list[str]:
        """Extract medically relevant keywords from normalized text."""
        normalized = self.normalize(text)
        keywords = []
        words = normalized.split()

        # Check against known medical terms
        medical_terms = set(self.HINGLISH_NORMALIZATIONS.keys()) | set(
            self.HINGLISH_NORMALIZATIONS.values()
        ) | set(self.EXPANSIONS.values())

        for word in words:
            clean = word.strip(".,!?;:")
            if clean in medical_terms:
                keywords.append(clean)

        return keywords

    def get_english_translation_hints(self, text: str) -> Optional[str]:
        """
        Provide English translation hints for Hinglish/Hindi words.
        Used to augment the LLM prompt with translation context.
        """
        words = text.lower().split()
        translations = []

        for word in words:
            clean = word.strip(".,!?;:")
            if clean in self.HINGLISH_NORMALIZATIONS:
                translations.append(
                    f"{clean}={self.HINGLISH_NORMALIZATIONS[clean]}"
                )

        return "; ".join(translations) if translations else None

    @staticmethod
    def _hinglish_markers() -> set[str]:
        """Common Hinglish words that indicate the text is Hinglish."""
        return {
            "hai", "ho", "raha", "rahi", "ko", "se", "mein", "ka", "ki",
            "ke", "nahi", "bahut", "abhi", "kal", "aaj", "kab", "kaise",
            "kya", "kaun", "chahiye", "ghar", "papa", "mummy", "dadi",
            "nana", "nani", "baad", "pehle", "din", "raat", "subah",
            "shaam", "wala", "wali", "ya", "aur", "par", "lekin",
        }
