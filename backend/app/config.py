"""
CareCompass AI — Application Configuration
Centralized settings management using pydantic-settings.
Loads from environment variables and .env file.
"""

from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # --- App ---
    app_name: str = "CareCompass AI"
    app_version: str = "0.1.0"
    app_env: str = "development"
    app_debug: bool = True
    app_host: str = "0.0.0.0"
    app_port: int = 8000

    # --- API Keys ---
    gemini_api_key: Optional[str] = None
    tinyfish_api_key: Optional[str] = None

    # --- Security ---
    jwt_secret_key: str = "dev-secret-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiry_minutes: int = 15
    rate_limit_per_minute: int = 100

    # --- Database ---
    database_url: Optional[str] = None  # e.g. postgresql+psycopg://user:pass@localhost:5432/carecompass

    # --- Supabase ---
    supabase_url: Optional[str] = None
    supabase_anon_key: Optional[str] = None
    supabase_service_role_key: Optional[str] = None  # server-side only; never expose to client
    # --- Redis ---
    redis_url: Optional[str] = None

    # --- Data Paths ---
    triage_dataset_path: str = "../triage_dataset.jsonl"
    caregivers_path: str = "../caregivers.csv"

    # --- AI/ML ---
    gemini_model: str = "gemini-2.0-flash"
    confidence_threshold: float = 0.6  # Below this → follow-up question
    max_matched_caregivers: int = 3

    # --- Caregiver Matching Weights ---
    weight_language: float = 0.25
    weight_distance: float = 0.25
    weight_skill: float = 0.20
    weight_rating: float = 0.10
    weight_availability: float = 0.10
    weight_tier: float = 0.05
    weight_experience: float = 0.05

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def data_dir(self) -> Path:
        """Resolve the data directory relative to the backend folder."""
        return Path(__file__).parent.parent.parent / "data"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance (singleton)."""
    return Settings()
