from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


RiskLevel = Literal["LOW", "MEDIUM", "HIGH"]


class VehicleInput(BaseModel):
    model_config = ConfigDict(extra="ignore")

    mileage: float | None = Field(default=None, ge=0)
    engine_hours: float | None = Field(default=None, ge=0)
    fault_codes: str | list[str] | int | float | None = None
    service_history: str | int | float | None = None
    usage_patterns: str | None = None

    vehicle_model: str | None = None
    maintenance_history: str | None = None
    reported_issues: float | None = Field(default=None, ge=0)
    vehicle_age: float | None = Field(default=None, ge=0)
    fuel_type: str | None = None
    transmission_type: str | None = None
    engine_size: float | None = Field(default=None, ge=0)
    odometer_reading: float | None = Field(default=None, ge=0)
    owner_type: str | None = None
    insurance_premium: float | None = Field(default=None, ge=0)
    service_history_score: float | None = Field(default=None, ge=0)
    accident_history: float | None = Field(default=None, ge=0)
    fuel_efficiency: float | None = Field(default=None, ge=0)
    tire_condition: str | None = None
    brake_condition: str | None = None
    battery_status: str | None = None
    days_since_service: float | None = Field(default=None, ge=0)
    days_until_warranty: float | None = Field(default=None, ge=0)


class PredictionItem(BaseModel):
    risk_level: RiskLevel
    confidence: float = Field(ge=0, le=1)
    feature_importance: dict[str, float]


class PredictionResponse(PredictionItem):
    total_records: int = 1
    predictions: list[PredictionItem] | None = None
    metadata: dict[str, Any] | None = None

