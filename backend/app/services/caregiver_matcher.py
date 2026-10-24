"""
CareCompass AI — Caregiver Matcher Service
Multi-signal caregiver matching and ranking engine optimizing for:
1. Clinical role & skill compatibility
2. Proximity (Haversine distance within service radius)
3. Language alignment (Hindi / English / Hinglish)
4. Quality & trust (Rating, Tier, Experience)
5. Live shift availability
"""

from __future__ import annotations

import logging
from typing import Optional

from app.config import get_settings
from app.models.schemas import CaregiverRecord, MatchedCaregiver
from app.utils.geo import distance_score, haversine_distance

logger = logging.getLogger("carecompass.matcher")
settings = get_settings()


class CaregiverMatcher:
    """
    Multi-Signal Caregiver Allocation Engine.
    Matches the highest-affinity caregivers for a given triage decision.
    """

    CARE_ROLE_MAP: dict[str, list[str]] = {
        "paramedic_home_visit": ["medic"],
        "home_nursing": ["medic"],
        "lab_test_home": ["phlebotomist"],
        "teleconsultation": ["doctor"],
        "emergency_112": [],  # Emergencies are NEVER routed to home caregivers
    }

    CARE_REQUIRED_SKILLS: dict[str, list[str]] = {
        "home_nursing": [
            "wound_dressing", "injection_im", "catheter_care",
            "vitals_monitoring", "nebulization", "post_surgical_care",
            "elderly_care",
        ],
        "paramedic_home_visit": [
            "vitals_monitoring", "injection_im", "wound_dressing", "nebulization",
        ],
        "lab_test_home": [
            "sample_collection", "home_phlebotomy",
        ],
        "teleconsultation": [
            "teleconsultation", "prescription", "report_review",
        ],
    }

    TIER_WEIGHTS: dict[str, float] = {
        "expert": 1.0,
        "advanced": 0.75,
        "standard": 0.50,
        "base": 0.25,
    }

    def __init__(self) -> None:
        self.w_lang = settings.weight_language
        self.w_dist = settings.weight_distance
        self.w_skill = settings.weight_skill
        self.w_rate = settings.weight_rating
        self.w_avail = settings.weight_availability
        self.w_tier = settings.weight_tier
        self.w_exp = settings.weight_experience

    def match(
        self,
        care_type: str,
        user_lat: float,
        user_lng: float,
        detected_language: str,
        caregivers: list[CaregiverRecord],
        keywords: list[str] | None = None,
        max_results: int = 3,
    ) -> list[MatchedCaregiver]:
        """
        Score, rank, and return top matched caregivers for a patient request.
        """
        # Emergencies NEVER get home caregivers
        if care_type == "emergency_112" or not care_type:
            return []

        allowed_roles = self.CARE_ROLE_MAP.get(care_type, [])
        if not allowed_roles:
            return []

        required_skills = self.CARE_REQUIRED_SKILLS.get(care_type, [])
        is_virtual = care_type == "teleconsultation"

        scored_candidates: list[tuple[float, CaregiverRecord, float, str]] = []

        for cg in caregivers:
            # 1. Filter: Role match
            if cg.role.lower() not in allowed_roles:
                continue

            # 2. Filter: Active status
            if not cg.active:
                continue

            # 3. Distance calculation
            dist_km = 0.0
            dist_s = 1.0
            if not is_virtual:
                dist_km = haversine_distance(user_lat, user_lng, cg.base_lat, cg.base_lng)
                # Hard filter: must be within reasonable operating radius (max_radius + 20% buffer)
                if dist_km > (cg.max_radius_km * 1.25):
                    continue
                dist_s = max(0.0, 1.0 - (dist_km / max(cg.max_radius_km, 1.0)))

            # 4. Language score
            lang_s = self._score_language(detected_language, cg.languages)

            # 5. Skill score
            skill_s = self._score_skills(cg.skills, required_skills, keywords)

            # 6. Rating score (normalized 0-1)
            rate_s = min(1.0, max(0.0, cg.rating / 5.0))

            # 7. Availability score
            avail_s = self._score_availability(cg.free_from, cg.free_until)

            # 8. Tier score (for medics)
            tier_s = self.TIER_WEIGHTS.get((cg.tier or "").lower(), 0.5)

            # 9. Experience score (capped at 10 years)
            exp_s = min(1.0, cg.experience_years / 10.0)

            # Composite Multi-Signal Score
            if is_virtual:
                # Teleconsultation ignores physical distance
                # Re-distribute distance weight to language, rating, and availability
                total_score = (
                    0.35 * lang_s
                    + 0.25 * rate_s
                    + 0.20 * skill_s
                    + 0.10 * avail_s
                    + 0.10 * exp_s
                )
            else:
                total_score = (
                    self.w_lang * lang_s
                    + self.w_dist * dist_s
                    + self.w_skill * skill_s
                    + self.w_rate * rate_s
                    + self.w_avail * avail_s
                    + self.w_tier * tier_s
                    + self.w_exp * exp_s
                )

            # Preferred language label for reasoning
            matched_lang = "Hindi" if "hindi" in detected_language.lower() or "hinglish" in detected_language.lower() else "English"
            if matched_lang not in cg.languages and cg.languages:
                matched_lang = cg.languages[0]

            scored_candidates.append((total_score, cg, dist_km, matched_lang))

        # Sort descending by composite score
        scored_candidates.sort(key=lambda x: x[0], reverse=True)

        # Build top-k MatchedCaregiver response objects
        matched_results: list[MatchedCaregiver] = []
        for score, cg, dist_km, matched_lang in scored_candidates[:max_results]:
            reason = self._build_match_reason(
                cg=cg,
                care_type=care_type,
                distance_km=dist_km,
                primary_language=matched_lang,
                is_virtual=is_virtual,
            )
            matched_results.append(
                MatchedCaregiver(
                    caregiver_id=cg.caregiver_id,
                    score=round(score, 2),
                    reason=reason,
                )
            )

        return matched_results

    def _score_language(self, user_lang: str, cg_languages: list[str]) -> float:
        """Score language compatibility between patient and caregiver."""
        user_lang_lower = user_lang.lower()
        cg_langs_lower = [l.lower() for l in cg_languages]

        if "hindi" in user_lang_lower or "hinglish" in user_lang_lower:
            if "hindi" in cg_langs_lower:
                return 1.0
            if "english" in cg_langs_lower:
                return 0.6
        elif "english" in user_lang_lower:
            if "english" in cg_langs_lower:
                return 1.0
            if "hindi" in cg_langs_lower:
                return 0.6

        return 0.5 if cg_languages else 0.0

    def _score_skills(
        self,
        cg_skills: list[str],
        required_skills: list[str],
        keywords: list[str] | None,
    ) -> float:
        """Calculate overlap between caregiver capabilities and clinical requirements."""
        if not required_skills:
            return 1.0

        cg_skills_set = set(s.lower() for s in cg_skills)
        req_skills_set = set(s.lower() for s in required_skills)

        # Baseline intersection
        matched = cg_skills_set.intersection(req_skills_set)
        base_score = len(matched) / max(len(req_skills_set), 1)

        # Boost if specific procedure keyword matches
        if keywords:
            for kw in keywords:
                kw_lower = kw.lower()
                for skill in cg_skills_set:
                    if kw_lower in skill or skill in kw_lower:
                        base_score = min(1.0, base_score + 0.15)
                        break

        return min(1.0, max(0.2, base_score))

    def _score_availability(self, free_from: str, free_until: str) -> float:
        """Score wider and convenient availability windows."""
        try:
            from_h = int(free_from.split(":")[0])
            until_h = int(free_until.split(":")[0])
            duration = until_h - from_h
            if duration <= 0:
                duration += 24
            return min(1.0, duration / 8.0)
        except Exception:
            return 0.7

    def _build_match_reason(
        self,
        cg: CaregiverRecord,
        care_type: str,
        distance_km: float,
        primary_language: str,
        is_virtual: bool,
    ) -> str:
        """Construct human-readable justification matching reference dataset style."""
        lang_str = f"{primary_language}-speaking"
        window_str = f"free {cg.free_from}–{cg.free_until}"

        if is_virtual:
            return f"{lang_str}, {window_str}, ★{cg.rating:.1f}"
        else:
            return f"{lang_str}, {distance_km:.1f} km away, {window_str}"
