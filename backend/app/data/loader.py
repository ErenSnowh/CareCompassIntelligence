"""
CareCompass AI — Data Loader
Loads and validates the triage dataset and caregiver roster.
Provides in-memory access to all data for the services.
"""

from __future__ import annotations

import csv
import json
import logging
from pathlib import Path
from typing import Any

from app.models.schemas import CaregiverRecord

logger = logging.getLogger(__name__)


class DataLoader:
    """Loads and caches all dataset files."""

    def __init__(self, triage_path: str, caregivers_path: str):
        self._triage_path = Path(triage_path)
        self._caregivers_path = Path(caregivers_path)
        self._triage_data: list[dict[str, Any]] = []
        self._caregivers: list[CaregiverRecord] = []
        self._loaded = False

    def load(self) -> None:
        """Load all datasets into memory."""
        self._load_triage_dataset()
        self._load_caregivers()
        self._loaded = True
        logger.info(
            "Data loaded: %d triage examples, %d caregivers",
            len(self._triage_data),
            len(self._caregivers),
        )

    def _load_triage_dataset(self) -> None:
        """Load triage_dataset.jsonl — one JSON object per line."""
        path = self._resolve_path(self._triage_path)
        if not path.exists():
            logger.warning("Triage dataset not found at %s", path)
            return

        self._triage_data = []
        with open(path, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                    self._triage_data.append(record)
                except json.JSONDecodeError as e:
                    logger.warning("Skipping line %d: %s", line_num, e)

        logger.info("Loaded %d triage examples from %s", len(self._triage_data), path)

    def _load_caregivers(self) -> None:
        """Load caregivers.csv into CaregiverRecord objects."""
        path = self._resolve_path(self._caregivers_path)
        if not path.exists():
            logger.warning("Caregivers file not found at %s", path)
            return

        self._caregivers = []
        with open(path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    caregiver = CaregiverRecord(
                        caregiver_id=row["caregiver_id"],
                        name=row["name"],
                        role=row["role"],
                        qualification=row["qualification"],
                        gender=row["gender"],
                        languages=[
                            lang.strip()
                            for lang in row["languages"].split(";")
                            if lang.strip()
                        ],
                        skills=[
                            skill.strip()
                            for skill in row["skills"].split(";")
                            if skill.strip()
                        ],
                        base_area=row["base_area"],
                        base_lat=float(row["base_lat"]),
                        base_lng=float(row["base_lng"]),
                        max_radius_km=float(row["max_radius_km"]),
                        tier=row.get("tier") or None,
                        rating=float(row["rating"]),
                        experience_years=int(row["experience_years"]),
                        free_from=row["free_from"],
                        free_until=row["free_until"],
                        active=row["active"].strip().lower() == "true",
                    )
                    self._caregivers.append(caregiver)
                except (ValueError, KeyError) as e:
                    logger.warning(
                        "Skipping caregiver row %s: %s",
                        row.get("caregiver_id", "?"),
                        e,
                    )

        logger.info("Loaded %d caregivers from %s", len(self._caregivers), path)

    def _resolve_path(self, path: Path) -> Path:
        """Resolve relative paths against the project root."""
        if path.is_absolute():
            return path
        # Resolve relative to the backend directory
        backend_dir = Path(__file__).parent.parent.parent
        resolved = (backend_dir / path).resolve()
        return resolved

    @property
    def triage_data(self) -> list[dict[str, Any]]:
        """Get all triage examples."""
        if not self._loaded:
            self.load()
        return self._triage_data

    @property
    def caregivers(self) -> list[CaregiverRecord]:
        """Get all caregiver records."""
        if not self._loaded:
            self.load()
        return self._caregivers

    @property
    def active_caregivers(self) -> list[CaregiverRecord]:
        """Get only active caregivers."""
        return [cg for cg in self.caregivers if cg.active]

    def get_caregiver(self, caregiver_id: str) -> CaregiverRecord | None:
        """Look up a caregiver by ID."""
        for cg in self.caregivers:
            if cg.caregiver_id == caregiver_id:
                return cg
        return None

    def get_triage_examples_by_care_type(
        self, care_type: str
    ) -> list[dict[str, Any]]:
        """Get training examples filtered by care_type."""
        return [
            ex
            for ex in self.triage_data
            if ex.get("response", {}).get("care_type") == care_type
        ]

    def get_statistics(self) -> dict[str, Any]:
        """Get dataset statistics for EDA / health checks."""
        care_type_counts: dict[str, int] = {}
        urgency_counts: dict[str, int] = {}
        language_counts: dict[str, int] = {}

        for ex in self.triage_data:
            ct = ex.get("response", {}).get("care_type") or "follow_up"
            care_type_counts[ct] = care_type_counts.get(ct, 0) + 1

            urg = ex.get("response", {}).get("urgency") or "null"
            urgency_counts[urg] = urgency_counts.get(urg, 0) + 1

            lang = ex.get("detected_language", "Unknown")
            language_counts[lang] = language_counts.get(lang, 0) + 1

        role_counts: dict[str, int] = {}
        for cg in self.caregivers:
            role_counts[cg.role] = role_counts.get(cg.role, 0) + 1

        return {
            "triage_examples": len(self.triage_data),
            "caregivers_total": len(self.caregivers),
            "caregivers_active": len(self.active_caregivers),
            "care_type_distribution": care_type_counts,
            "urgency_distribution": urgency_counts,
            "language_distribution": language_counts,
            "caregiver_role_distribution": role_counts,
        }
