from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


RiskLevel = Literal["LOW", "MEDIUM", "HIGH"]
InsightDirection = Literal["RISK_UP", "RISK_DOWN", "NEUTRAL"]
RecommendationPriority = Literal["HIGH", "MEDIUM", "LOW"]
InsightSource = Literal["RULES", "GENAI_LLM"]


class VehicleInput(BaseModel):
    """
    Flexible input schema:
    - Supports Milestone-1 required fields.
    - Also supports optional model-native fields for higher fidelity.
    """

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
    risk_probability: float = Field(ge=0, le=1)
    confidence: float = Field(ge=0, le=1)
    feature_importance: dict[str, float]
    insight_summary: str | None = None
    insight_source: InsightSource = "RULES"
    insight_drivers: list["InsightDriver"] = Field(default_factory=list)
    recommendations: list["RecommendationItem"] = Field(default_factory=list)
    data_warnings: list[str] = Field(default_factory=list)


class InsightDriver(BaseModel):
    factor: str
    observed_value: str
    direction: InsightDirection
    impact: float = Field(ge=0, le=1)
    explanation: str


class RecommendationItem(BaseModel):
    priority: RecommendationPriority
    action: str
    rationale: str


class PredictionResponse(PredictionItem):
    total_records: int = 1
    predictions: list[PredictionItem] | None = None
    metadata: dict[str, Any] | None = None
