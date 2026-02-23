from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_prefix": "FLEET_"}

    model_path: Path = Path(__file__).resolve().parents[2] / "model" / "vehicle_maintenance_pipeline.pkl"
    cors_origins: list[str] = ["*"]
    debug: bool = False


settings = Settings()
