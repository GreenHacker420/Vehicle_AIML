from __future__ import annotations

import os
from pathlib import Path

from pydantic_settings import BaseSettings


def _find_model_file() -> Path:
    """Try several candidate locations for the model pickle file."""
    candidates = [
        # Local development: config.py → app/ → backend/ → repo-root/
        Path(__file__).resolve().parents[2] / "model" / "vehicle_maintenance_pipeline.pkl",
        # Vercel: cwd is the repo root
        Path(os.getcwd()) / "model" / "vehicle_maintenance_pipeline.pkl",
        # Vercel alt: relative to the serverless function directory
        Path(__file__).resolve().parents[3] / "model" / "vehicle_maintenance_pipeline.pkl",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    # Return first candidate as default (will raise a clear error later)
    return candidates[0]


class Settings(BaseSettings):
    model_config = {"env_prefix": "FLEET_"}

    model_path: Path = _find_model_file()
    cors_origins: list[str] = ["*"]
    debug: bool = False


settings = Settings()
