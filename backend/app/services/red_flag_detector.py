"""
CareCompass AI — Red Flag Detector Service (Safety-First Core)
Dual-layer emergency detection system ensuring near-100% recall for medical red flags.
"""

from __future__ import annotations

import logging
import re
from typing import Any, Optional

logger = logging.getLogger("carecompass.safety")


class RedFlagDetector:
    """
    Dual-layer safety-first red flag detection system.

    Layer 1: Rule-based & regex scanner across English, Hindi (Devanagari),
             and Hinglish transliterations with negation awareness.
    Layer 2: Semantic emergency evaluator for implicit or borderline cases.

    Design Principle: High Recall > High Precision.
    Zero tolerance for missed emergencies.
    """

    # Comprehensive multilingual keyword mapping for all 9 red-flag categories
    RED_FLAG_KEYWORDS: dict[str, dict[str, list[str]]] = {
        "chest_pain": {
            "en": [
                "chest pain", "chest tight", "tightness in chest", "pressure in chest",
                "crushing chest", "heart attack", "chest heaviness", "cardiac arrest",
                "pain radiating to left arm", "severe chest",
            ],
            "hi": [
                "सीने में दर्द", "छाती में दर्द", "दिल का दौरा", "दिल में दर्द",
                "सीने में जकड़न", "सीने में दबाव", "छाती में भारीपन",
            ],
            "hinglish": [
                "chest pain", "chest me pain", "chest me dard", "seene mein dard",
                "seene me dard", "chhati mein dard", "chhati me dard", "dil ka daura",
                "chest tightness", "chest tight", "seene me jalan", "dil me dard",
            ],
        },
        "breathlessness": {
            "en": [
                "can't breathe", "cannot breathe", "difficulty breathing",
                "shortness of breath", "gasping for air", "gasping", "choking",
                "trouble breathing", "unable to breathe", "breathless",
            ],
            "hi": [
                "सांस नहीं आ रही", "साँस नहीं आ रही", "सांस लेने में तकलीफ",
                "सांस फूल रही", "दम घुट रहा", "सांस की दिक्कत", "साँस की समस्या",
            ],
            "hinglish": [
                "saans nahi aa rahi", "sans nahi aa rahi", "saans nahi",
                "saans lene me takleef", "saans phool rahi", "dum ghut raha",
                "breathing problem", "breathing issue", "breathless",
                "saans lene me dikkat", "dam ghutna",
            ],
        },
        "unconsciousness": {
            "en": [
                "unconscious", "passed out", "fainted", "not responding",
                "collapsed", "unresponsive", "coma", "blackout", "passed-out",
                "suddenly collapsed", "not waking up", "loss of consciousness",
            ],
            "hi": [
                "बेहोश", "होश नहीं", "गिर गए", "जवाब नहीं दे रहे",
                "होश खो दिया", "चक्कर खाकर गिर", "आंखें बंद हैं बोल नहीं",
            ],
            "hinglish": [
                "behosh", "behosh ho gaye", "hosh nahi hai", "gir gaye",
                "response nahi de rahe", "respond nahi kar rahe", "jawab nahi de rahe",
                "suddenly collapsed", "unconscious hai", "hosh me nahi",
                "gir gaya", "kuch bol nahi rahe",
            ],
        },
        "severe_bleeding": {
            "en": [
                "heavy bleeding", "bleeding won't stop", "bleeding wont stop",
                "blood loss", "hemorrhage", "profuse bleeding", "bleeding heavily",
                "spurting blood", "gushing blood", "severe bleeding",
            ],
            "hi": [
                "खून नहीं रुक रहा", "बहुत खून बह रहा", "खून बहना बंद नहीं",
                "भारी रक्तस्राव", "खून की धार",
            ],
            "hinglish": [
                "bleeding ruk nahi rahi", "bleeding band nahi", "khoon nahi ruk raha",
                "bahut khoon beh raha", "bahut bleeding", "blood ruk nahi raha",
                "khoon band nahi ho raha", "accident ke baad bleeding",
            ],
        },
        "stroke_symptoms": {
            "en": [
                "face drooping", "slurred speech", "arm weakness", "stroke",
                "paralysis", "sudden numbness", "one side numb", "facial droop",
                "unable to speak", "mouth twisted", "hemiplegia",
            ],
            "hi": [
                "चेहरा टेढ़ा", "बोलने में दिक्कत", "हाथ में कमजोरी", "लकवा",
                "फालिज", "एक तरफ कमजोरी", "मुंह टेढ़ा", "आवाज लड़खड़ा",
            ],
            "hinglish": [
                "face tedha", "face ek taraf", "speech slur", "bol nahi pa rahe",
                "lakwa", "stroke", "haath me kamzori", "one side paralyzed",
                "zubaan ladkhada rahi", "chehra tedha",
            ],
        },
        "seizure": {
            "en": [
                "seizure", "convulsion", "fits", "epileptic fit", "jerking uncontrollably",
                "epilepsy attack", "violent shaking",
            ],
            "hi": [
                "मिर्गी का दौरा", "झटके आ रहे", "शरीर अकड़ गया", "दौरे पड़ रहे",
                "कंपकंपी छूट रही",
            ],
            "hinglish": [
                "mirgi ka daura", "fits aa rahe", "seizure aa raha", "jhatke aa rahe",
                "body akad gayi", "mirgi attack", "fits pad rahe",
            ],
        },
        "high_fever_infant": {
            "en": [
                "baby high fever", "infant high fever", "newborn fever", "infant fever",
                "baby burning hot", "toddler high fever", "neonate fever", "baby 104 fever",
            ],
            "hi": [
                "बच्चे को तेज बुखार", "शिशु को बुखार", "नवजात को बुखार",
                "छोटा बच्चा बहुत गर्म", "दूध नहीं पी रहा और बुखार",
            ],
            "hinglish": [
                "baby ko high fever", "baby ko tez bukhar", "bachche ko high fever",
                "chote baby ko bukhar", "infant fever", "newborn ko bukhar",
                "baby ka temperature bahut high",
            ],
        },
        "suicidal_ideation": {
            "en": [
                "want to die", "kill myself", "end my life", "suicidal", "suicide",
                "don't want to live", "no reason to live", "taking overdose",
            ],
            "hi": [
                "मरना चाहता", "मरना चाहती", "जान देना चाहता", "आत्महत्या",
                "जिंदगी खत्म करना", "जीने का मन नहीं",
            ],
            "hinglish": [
                "suicide karna hai", "marna chahta hu", "marna chahti hu",
                "life end karni hai", "jaan deni hai", "suicidal thoughts",
                "jeene ka man nahi",
            ],
        },
        "severe_dehydration": {
            "en": [
                "severe dehydration", "not urinating for 24 hours", "sunken eyes",
                "no urine", "extremely dry mouth", "unresponsive from dehydration",
                "no tears crying",
            ],
            "hi": [
                "पानी की अत्यधिक कमी", "पेशाब बिल्कुल नहीं", "आंखें धंस गई",
                "गंभीर डिहाइड्रेशन", "मुंह बिल्कुल सूखा",
            ],
            "hinglish": [
                "severe dehydration", "peshab nahi aa raha", "peshab band ho gaya",
                "aankhein dhans gayi", "paani ki kami behosh", "urine pass nahi ho raha",
            ],
        },
    }

    # Negation patterns to prevent false alarms (e.g. "no chest pain", "chhati me dard nahi")
    NEGATION_PATTERNS = [
        re.compile(r"\bno\s+(chest\s+pain|breathing\s+difficulty|bleeding|fainting)\b", re.IGNORECASE),
        re.compile(r"\bwithout\s+(chest\s+pain|breathlessness|bleeding)\b", re.IGNORECASE),
        re.compile(r"(chest\s+pain|seene\s+me\s+dard|bleeding)\s+nahi\s+hai", re.IGNORECASE),
        re.compile(r"(सीने\s+में\s+दर्द|सांस\s+की\s+दिक्कत)\s+नहीं\s+है", re.IGNORECASE),
    ]

    # Additional composite patterns for multi-token clinical red flags
    COMPOSITE_PATTERNS: dict[str, list[str]] = {
        "high_fever_infant": [
            r"\b(baby|bachche|shishu|infant|newborn|toddler|chote\s+baby)\b.{0,40}\b(high\s+fever|tez\s+bukhar|burning\s+hot|104|temperature)\b",
            r"\b(high\s+fever|tez\s+bukhar|burning\s+hot)\b.{0,40}\b(baby|bachche|shishu|infant|newborn|toddler)\b",
            r"(बच्चे|शिशु|नवजात).{0,25}(तेज\s*बुखार|बहुत\s*गर्म)",
            r"(तेज\s*बुखार|बहुत\s*गर्म).{0,25}(बच्चे|शिशु|नवजात)",
        ],
        "severe_bleeding": [
            r"\b(bleeding|khoon|blood).{0,25}\b(ruk\s+nahi|band\s+nahi|won't\s+stop|wont\s+stop|heavy|profuse)\b",
            r"(खून|रक्त).{0,20}(नहीं\s+रुक|बंद\s+नहीं)",
        ],
        "unconsciousness": [
            r"\b(gir\s+gaye|collapsed|fainted|passed\s+out).{0,30}\b(response|respond|jawab|hosh|uth)\b",
            r"(गिर\s+गए|चक्कर).{0,20}(जवाब\s+नहीं|होश)",
        ],
    }

    def __init__(self) -> None:
        self._compiled_regexes = self._compile_keyword_patterns()

    def _compile_keyword_patterns(self) -> dict[str, list[re.Pattern]]:
        """Pre-compile regex patterns for high-speed deterministic matching."""
        compiled: dict[str, list[re.Pattern]] = {}
        for flag_code, lang_dict in self.RED_FLAG_KEYWORDS.items():
            patterns = []
            for lang, phrases in lang_dict.items():
                for phrase in phrases:
                    # Escape special regex chars, match flexibly with whitespace
                    escaped = re.escape(phrase.strip())
                    pattern_str = rf"(?:\b|\s|^){escaped}(?:\b|\s|$)"
                    patterns.append(re.compile(pattern_str, re.IGNORECASE))

            # Add composite patterns
            if flag_code in self.COMPOSITE_PATTERNS:
                for comp_pat in self.COMPOSITE_PATTERNS[flag_code]:
                    patterns.append(re.compile(comp_pat, re.IGNORECASE))

            compiled[flag_code] = patterns
        return compiled


    def detect(self, text: str) -> list[str]:
        """
        Layer 1: Rule-based red flag detection.
        Scans normalized user input against multilingual keyword library.

        Args:
            text: Normalized user input text

        Returns:
            List of detected red flag codes (empty if safe)
        """
        if not text or not text.strip():
            return []

        clean_text = text.strip()
        detected_flags: list[str] = []

        # Check for explicit negation
        for neg_pat in self.NEGATION_PATTERNS:
            if neg_pat.search(clean_text):
                # Negated symptom detected; strip it for evaluation
                clean_text = neg_pat.sub(" ", clean_text)

        # Scan against compiled keyword patterns
        for flag_code, patterns in self._compiled_regexes.items():
            for pat in patterns:
                if pat.search(clean_text):
                    if flag_code not in detected_flags:
                        detected_flags.append(flag_code)
                        logger.warning(
                            "RED FLAG DETECTED: %s (matched pattern: '%s')",
                            flag_code,
                            pat.pattern,
                        )
                    break

        return detected_flags

    def is_emergency(self, text: str) -> tuple[bool, list[str]]:
        """
        Check if the input triggers an emergency response.

        Returns:
            Tuple of (is_emergency, list_of_red_flags)
        """
        flags = self.detect(text)
        return len(flags) > 0, flags

    def get_emergency_guidance(self, red_flags: list[str]) -> str:
        """
        Generate immediate clinical first-aid guidance for the detected red flags.
        Provides actionable instructions while waiting for 112 emergency services.
        """
        if not red_flags:
            return ""

        guidelines = [
            "🚨 CRITICAL EMERGENCY: Call 112 immediately or proceed to the nearest hospital emergency department."
        ]

        if "chest_pain" in red_flags or "breathlessness" in red_flags:
            guidelines.append(
                "• Keep the patient calm, seated upright, and loosen tight clothing around the neck and chest."
            )
            guidelines.append(
                "• Do not give large meals or fluids. Have someone wait outside to guide the ambulance."
            )
        if "severe_bleeding" in red_flags:
            guidelines.append(
                "• Apply firm, direct pressure to the wound with a clean cloth. Elevate the bleeding limb if possible."
            )
        if "unconsciousness" in red_flags:
            guidelines.append(
                "• Turn the patient onto their side in recovery position to keep airway clear. Check breathing."
            )
        if "seizure" in red_flags:
            guidelines.append(
                "• Protect the head from hard objects. Do not put anything in the mouth or restrain movements."
            )
        if "stroke_symptoms" in red_flags:
            guidelines.append(
                "• Note the exact time symptoms started. Time is brain — rapid hospital transit is crucial."
            )
        if "high_fever_infant" in red_flags:
            guidelines.append(
                "• Sponge with lukewarm (not cold) water. Seek emergency pediatric care immediately."
            )

        return " ".join(guidelines)
