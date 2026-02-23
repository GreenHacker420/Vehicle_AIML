from __future__ import annotations

import io
import re
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable

import joblib
import numpy as np
import pandas as pd
from fastapi import HTTPException, UploadFile, status
from sklearn.pipeline import Pipeline

from app.schemas.prediction import (
    InsightDriver,
    PredictionItem,
    PredictionResponse,
    RecommendationItem,
    VehicleInput,
)
from app.services.llm_insight_service import LLMInsightService


class PredictionService:
    """
    Loads the trained sklearn pipeline once and serves JSON / CSV predictions.
    """

    MODEL_FILE = Path(__file__).resolve().parents[3] / "model" / "vehicle_maintenance_pipeline.pkl"

    _REQUIRED_MINIMUM_FIELDS = {
        "mileage",
        "engine_hours",
        "fault_codes",
        "service_history",
        "usage_patterns",
    }

    _MODEL_COLUMNS_FALLBACK = [
        "Vehicle_Model",
        "Mileage",
        "Maintenance_History",
        "Reported_Issues",
        "Vehicle_Age",
        "Fuel_Type",
        "Transmission_Type",
        "Engine_Size",
        "Odometer_Reading",
        "Owner_Type",
        "Insurance_Premium",
        "Service_History",
        "Accident_History",
        "Fuel_Efficiency",
        "Tire_Condition",
        "Brake_Condition",
        "Battery_Status",
        "Days_Since_Service",
        "Days_Until_Warranty",
    ]

    def __init__(self, model_path: Path | None = None) -> None:
        self.model_path = model_path or self.MODEL_FILE
        if not self.model_path.exists():
            raise RuntimeError(f"Trained model file not found at: {self.model_path}")

        loaded = joblib.load(self.model_path)
        if not isinstance(loaded, Pipeline):
            raise RuntimeError("The loaded model artifact is not an sklearn Pipeline.")

        self.pipeline = loaded
        self.required_columns: list[str] = list(
            getattr(self.pipeline, "feature_names_in_", self._MODEL_COLUMNS_FALLBACK)
        )
        self._feature_importance = self._extract_feature_importance()
        self.llm_insight_service = LLMInsightService()

    async def parse_csv_upload(self, file: UploadFile) -> list[dict[str, Any]]:
        if not file.filename:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing CSV filename.")
        if not file.filename.lower().endswith(".csv"):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only CSV uploads are supported.")

        raw = await file.read()
        if not raw:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded CSV is empty.")

        try:
            frame = pd.read_csv(io.StringIO(raw.decode("utf-8-sig")))
        except Exception as exc:  # pragma: no cover - defensive parse errors
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to parse CSV: {exc}",
            ) from exc

        if frame.empty:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="CSV has no rows.")

        records = frame.replace({np.nan: None}).to_dict(orient="records")
        return [self._normalize_payload(record) for record in records]

    def predict_single(self, payload: dict[str, Any]) -> PredictionResponse:
        normalized = self._normalize_payload(payload)
        row = self._build_model_row(normalized)

        inference_frame = pd.DataFrame([row], columns=self.required_columns)
        probability = float(self.pipeline.predict_proba(inference_frame)[0][1])

        item = self._build_prediction_item(row=row, probability=probability)
        return PredictionResponse(
            **item.model_dump(),
            metadata={
                "feature_importance_type": "global_model_weight",
                "insight_method": "rule_based_operational_explanation"
                if item.insight_source == "RULES"
                else "genai_llm_plus_rules",
            },
        )

    def predict_many(self, payloads: Iterable[dict[str, Any]]) -> PredictionResponse:
        normalized_payloads = [self._normalize_payload(item) for item in payloads]
        if not normalized_payloads:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No data rows were provided for prediction.",
            )

        model_rows = [self._build_model_row(payload) for payload in normalized_payloads]
        frame = pd.DataFrame(model_rows, columns=self.required_columns)
        probabilities = self.pipeline.predict_proba(frame)[:, 1]

        prediction_items = [
            self._build_prediction_item(row=row, probability=float(probability))
            for row, probability in zip(model_rows, probabilities)
        ]

        # Summarize with the highest-risk item to keep top-level response contract simple.
        summary = max(
            prediction_items,
            key=lambda item: (self._risk_rank(item.risk_level), item.confidence),
        )

        return PredictionResponse(
            risk_level=summary.risk_level,
            risk_probability=summary.risk_probability,
            confidence=summary.confidence,
            feature_importance=summary.feature_importance,
            insight_summary=summary.insight_summary,
            insight_drivers=summary.insight_drivers,
            recommendations=summary.recommendations,
            data_warnings=summary.data_warnings,
            total_records=len(prediction_items),
            predictions=prediction_items,
            metadata={
                "summary_strategy": "highest_risk",
                "feature_importance_type": "global_model_weight",
                "insight_method": "rule_based_operational_explanation"
                if summary.insight_source == "RULES"
                else "genai_llm_plus_rules",
            },
        )

    def _build_prediction_item(self, *, row: dict[str, Any], probability: float) -> PredictionItem:
        risk_level = self._map_risk_level(probability)
        insight = self._generate_insight_bundle(row=row, probability=probability, risk_level=risk_level)
        insight_source = "RULES"

        llm_payload = self.llm_insight_service.generate(
            risk_level=risk_level,
            risk_probability=probability,
            rule_summary=insight["summary"],
            row=row,
            drivers=[driver.model_dump() for driver in insight["drivers"]],
        )
        if llm_payload:
            insight_source = "GENAI_LLM"
            insight["summary"] = llm_payload.get("summary", insight["summary"])
            insight["recommendations"] = self._merge_llm_recommendations(
                existing=insight["recommendations"],
                llm_recommendations=llm_payload.get("recommendations", []),
                risk_level=risk_level,
            )

        return PredictionItem(
            risk_level=risk_level,
            risk_probability=round(probability, 4),
            confidence=round(self._confidence(probability), 4),
            feature_importance=self._feature_importance,
            insight_summary=insight["summary"],
            insight_source=insight_source,
            insight_drivers=insight["drivers"],
            recommendations=insight["recommendations"],
            data_warnings=insight["warnings"],
        )

    @staticmethod
    def _risk_rank(risk_level: str) -> int:
        return {"LOW": 0, "MEDIUM": 1, "HIGH": 2}[risk_level]

    @staticmethod
    def _map_risk_level(probability: float) -> str:
        if probability < 0.3:
            return "LOW"
        if probability < 0.7:
            return "MEDIUM"
        return "HIGH"

    @staticmethod
    def _confidence(probability: float) -> float:
        # Confidence = max class probability.
        return max(probability, 1.0 - probability)

    def _build_model_row(self, payload: dict[str, Any]) -> dict[str, Any]:
        has_minimum = all(field in payload and payload[field] not in (None, "") for field in self._REQUIRED_MINIMUM_FIELDS)
        has_model_fields = any(self._normalize_key(column) in payload for column in self.required_columns)
        if not (has_minimum or has_model_fields):
            required = ", ".join(sorted(self._REQUIRED_MINIMUM_FIELDS))
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    "Input must include either model-compatible fields or minimum fields: "
                    f"{required}."
                ),
            )

        usage_pattern = str(payload.get("usage_patterns") or "normal").strip().lower()
        usage_band = self._classify_usage(usage_pattern)

        mileage = self._to_float(
            self._pick(payload, "mileage", "odometer_reading"),
            default=50000.0,
            min_value=0.0,
        )
        engine_hours = self._to_float(payload.get("engine_hours"), default=max(250.0, mileage / 35.0), min_value=0.0)

        issues_raw = self._pick(payload, "fault_codes", "reported_issues")
        reported_issues = self._extract_fault_code_count(issues_raw)
        if payload.get("reported_issues") is not None:
            reported_issues = self._to_float(payload.get("reported_issues"), default=reported_issues, min_value=0.0)

        service_raw = self._pick(payload, "service_history_score", "service_history", "maintenance_history")
        service_score = self._derive_service_history_score(service_raw)
        if payload.get("service_history_score") is not None:
            service_score = self._to_float(payload.get("service_history_score"), default=service_score, min_value=0.0)

        maintenance_history = self._derive_maintenance_history_category(service_raw)
        if payload.get("maintenance_history") is not None:
            maintenance_history = self._normalize_maintenance_category(str(payload["maintenance_history"]))

        vehicle_age = self._to_float(payload.get("vehicle_age"), default=max(0.0, engine_hours / 700.0), min_value=0.0)
        odometer_reading = self._to_float(payload.get("odometer_reading"), default=mileage, min_value=0.0)
        engine_size = self._to_float(
            payload.get("engine_size"),
            default=2.2 if usage_band == "heavy" else 1.8,
            min_value=0.8,
            max_value=8.0,
        )
        accident_history = self._to_float(
            payload.get("accident_history"),
            default=1.0 if "accident" in usage_pattern else 0.0,
            min_value=0.0,
            max_value=10.0,
        )
        days_since_service = self._to_float(
            payload.get("days_since_service"),
            default=self._derive_days_since_service(service_score, usage_band),
            min_value=0.0,
        )
        days_until_warranty = self._to_float(
            payload.get("days_until_warranty"),
            default=max(0.0, (7.0 - min(7.0, vehicle_age)) * 365.0),
            min_value=0.0,
        )
        fuel_efficiency = self._to_float(
            payload.get("fuel_efficiency"),
            default=self._derive_fuel_efficiency(engine_size, usage_band),
            min_value=5.0,
            max_value=80.0,
        )
        insurance_premium = self._to_float(
            payload.get("insurance_premium"),
            default=self._derive_insurance_premium(vehicle_age, accident_history, usage_band),
            min_value=100.0,
        )

        default_condition = self._infer_component_condition(
            mileage=mileage,
            reported_issues=reported_issues,
            days_since_service=days_since_service,
            usage_band=usage_band,
        )
        tire_condition = self._normalize_tire_or_brake(
            str(payload.get("tire_condition") or default_condition)
        )
        brake_condition = self._normalize_tire_or_brake(
            str(payload.get("brake_condition") or default_condition)
        )
        battery_status = self._normalize_battery_status(
            str(payload.get("battery_status") or ("Weak" if default_condition == "Worn Out" else "Good"))
        )

        owner_type = str(payload.get("owner_type") or ("Commercial" if usage_band == "heavy" else "Individual")).strip().title()
        vehicle_model = str(payload.get("vehicle_model") or "Sedan").strip().title()
        fuel_type = str(payload.get("fuel_type") or "Petrol").strip().title()
        transmission_type = str(payload.get("transmission_type") or "Automatic").strip().title()

        row = {
            "Vehicle_Model": vehicle_model,
            "Mileage": mileage,
            "Maintenance_History": maintenance_history,
            "Reported_Issues": reported_issues,
            "Vehicle_Age": vehicle_age,
            "Fuel_Type": fuel_type,
            "Transmission_Type": transmission_type,
            "Engine_Size": engine_size,
            "Odometer_Reading": odometer_reading,
            "Owner_Type": owner_type,
            "Insurance_Premium": insurance_premium,
            "Service_History": service_score,
            "Accident_History": accident_history,
            "Fuel_Efficiency": fuel_efficiency,
            "Tire_Condition": tire_condition,
            "Brake_Condition": brake_condition,
            "Battery_Status": battery_status,
            "Days_Since_Service": days_since_service,
            "Days_Until_Warranty": days_until_warranty,
        }

        # Ensure compatibility with trained pipeline order and strict column set.
        return {column: row[column] for column in self.required_columns}

    @staticmethod
    def _derive_days_since_service(service_score: float, usage_band: str) -> float:
        if service_score >= 8:
            return 45.0 if usage_band == "heavy" else 30.0
        if service_score >= 5:
            return 120.0
        if service_score >= 3:
            return 210.0
        return 320.0

    @staticmethod
    def _derive_fuel_efficiency(engine_size: float, usage_band: str) -> float:
        base = 32.0 - (engine_size - 1.5) * 4.0
        if usage_band == "heavy":
            base -= 4.0
        elif usage_band == "moderate":
            base -= 1.5
        return max(10.0, round(base, 2))

    @staticmethod
    def _derive_insurance_premium(vehicle_age: float, accident_history: float, usage_band: str) -> float:
        premium = 650.0 + vehicle_age * 35.0 + accident_history * 180.0
        if usage_band == "heavy":
            premium += 220.0
        return round(max(300.0, premium), 2)

    @staticmethod
    def _infer_component_condition(
        mileage: float,
        reported_issues: float,
        days_since_service: float,
        usage_band: str,
    ) -> str:
        score = 0
        if mileage >= 150000:
            score += 2
        elif mileage >= 80000:
            score += 1

        if reported_issues >= 6:
            score += 2
        elif reported_issues >= 2:
            score += 1

        if days_since_service >= 240:
            score += 1
        if usage_band == "heavy":
            score += 1

        if score >= 4:
            return "Worn Out"
        if score >= 2:
            return "Good"
        return "New"

    @staticmethod
    def _normalize_tire_or_brake(value: str) -> str:
        normalized = value.strip().lower()
        if normalized in {"worn", "worn out", "poor", "bad"}:
            return "Worn Out"
        if normalized in {"new", "excellent"}:
            return "New"
        return "Good"

    @staticmethod
    def _normalize_battery_status(value: str) -> str:
        normalized = value.strip().lower()
        if normalized in {"weak", "low", "degraded", "poor"}:
            return "Weak"
        if normalized in {"new", "fresh"}:
            return "New"
        return "Good"

    @staticmethod
    def _derive_service_history_score(value: Any) -> float:
        if value is None:
            return 5.0
        number = PredictionService._to_float(value, default=np.nan, min_value=0.0)
        if not np.isnan(number):
            return float(min(number, 12.0))

        normalized = str(value).strip().lower()
        if normalized in {"excellent", "good", "regular", "consistent", "on_time"}:
            return 9.0
        if normalized in {"average", "moderate", "occasional"}:
            return 5.0
        if normalized in {"poor", "irregular", "none", "overdue"}:
            return 2.0
        return 5.0

    @staticmethod
    def _derive_maintenance_history_category(value: Any) -> str:
        if value is None:
            return "Average"

        number = PredictionService._to_float(value, default=np.nan, min_value=0.0)
        if not np.isnan(number):
            if number >= 8:
                return "Good"
            if number >= 4:
                return "Average"
            return "Poor"
        return PredictionService._normalize_maintenance_category(str(value))

    @staticmethod
    def _normalize_maintenance_category(value: str) -> str:
        normalized = value.strip().lower()
        if normalized in {"good", "excellent", "regular", "consistent"}:
            return "Good"
        if normalized in {"poor", "bad", "none", "overdue"}:
            return "Poor"
        return "Average"

    @staticmethod
    def _classify_usage(usage_pattern: str) -> str:
        text = usage_pattern.lower()
        heavy_tokens = {"heavy", "commercial", "longhaul", "aggressive", "city", "high"}
        moderate_tokens = {"moderate", "mixed", "normal", "daily"}
        if any(token in text for token in heavy_tokens):
            return "heavy"
        if any(token in text for token in moderate_tokens):
            return "moderate"
        return "light"

    @staticmethod
    def _extract_fault_code_count(value: Any) -> float:
        if value is None:
            return 0.0
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return max(float(value), 0.0)
        if isinstance(value, list):
            return float(len([entry for entry in value if str(entry).strip()]))

        text = str(value).strip().lower()
        if text in {"", "none", "na", "n/a", "null"}:
            return 0.0
        tokens = [token for token in re.split(r"[,\s;|]+", text) if token]
        return float(len(tokens))

    @staticmethod
    def _to_float(
        value: Any,
        *,
        default: float,
        min_value: float | None = None,
        max_value: float | None = None,
    ) -> float:
        number = default
        try:
            if value not in (None, ""):
                number = float(value)
        except (TypeError, ValueError):
            number = default

        if min_value is not None:
            number = max(number, min_value)
        if max_value is not None:
            number = min(number, max_value)
        return number

    @staticmethod
    def _normalize_key(key: str) -> str:
        return re.sub(r"[^a-z0-9]+", "_", key.strip().lower()).strip("_")

    def _generate_insight_bundle(
        self,
        *,
        row: dict[str, Any],
        probability: float,
        risk_level: str,
    ) -> dict[str, Any]:
        mileage = float(row.get("Mileage", 0.0))
        issues = float(row.get("Reported_Issues", 0.0))
        service_score = float(row.get("Service_History", 0.0))
        accident_history = float(row.get("Accident_History", 0.0))
        days_since_service = float(row.get("Days_Since_Service", 0.0))
        engine_hours = float(row.get("Vehicle_Age", 0.0)) * 700.0

        tire_condition = str(row.get("Tire_Condition", "Good"))
        brake_condition = str(row.get("Brake_Condition", "Good"))
        battery_status = str(row.get("Battery_Status", "Good"))
        owner_type = str(row.get("Owner_Type", "Individual"))

        drivers: list[InsightDriver] = []

        drivers.append(
            self._issue_driver(issues)
        )
        drivers.append(
            self._service_driver(service_score)
        )
        drivers.append(
            self._service_recency_driver(days_since_service)
        )
        drivers.append(
            self._component_driver("Brake condition", brake_condition)
        )
        drivers.append(
            self._component_driver("Tire condition", tire_condition)
        )
        drivers.append(
            self._battery_driver(battery_status)
        )
        drivers.append(
            self._accident_driver(accident_history)
        )
        drivers.append(
            self._mileage_driver(mileage)
        )
        drivers.append(
            self._usage_driver(owner_type)
        )

        ordered_drivers = sorted(
            drivers,
            key=lambda item: (
                item.impact,
                1 if item.direction == "RISK_UP" else 0,
            ),
            reverse=True,
        )[:6]

        warnings = self._data_quality_warnings(
            mileage=mileage,
            engine_hours=engine_hours,
            reported_issues=issues,
        )
        recommendations = self._recommendations_from_drivers(ordered_drivers, risk_level)
        summary = self._build_insight_summary(
            probability=probability,
            risk_level=risk_level,
            drivers=ordered_drivers,
        )

        return {
            "summary": summary,
            "drivers": ordered_drivers,
            "recommendations": recommendations,
            "warnings": warnings,
        }

    @staticmethod
    def _issue_driver(issues: float) -> InsightDriver:
        if issues >= 5:
            return InsightDriver(
                factor="Reported issues",
                observed_value=f"{issues:.0f} active fault codes",
                direction="RISK_UP",
                impact=0.95,
                explanation="Multiple active fault codes strongly increase near-term maintenance risk.",
            )
        if issues >= 2:
            return InsightDriver(
                factor="Reported issues",
                observed_value=f"{issues:.0f} active fault codes",
                direction="RISK_UP",
                impact=0.72,
                explanation="More than one active fault code indicates unresolved system health issues.",
            )
        if issues == 1:
            return InsightDriver(
                factor="Reported issues",
                observed_value="1 active fault code",
                direction="RISK_UP",
                impact=0.42,
                explanation="A single active fault code adds moderate risk until it is resolved.",
            )
        return InsightDriver(
            factor="Reported issues",
            observed_value="No active fault codes",
            direction="RISK_DOWN",
            impact=0.45,
            explanation="No active fault codes is a stabilizing signal for maintenance risk.",
        )

    @staticmethod
    def _service_driver(service_score: float) -> InsightDriver:
        if service_score <= 3:
            return InsightDriver(
                factor="Service history",
                observed_value=f"Score {service_score:.1f}/10",
                direction="RISK_UP",
                impact=0.8,
                explanation="Poor maintenance discipline increases risk of component failure.",
            )
        if service_score < 7:
            return InsightDriver(
                factor="Service history",
                observed_value=f"Score {service_score:.1f}/10",
                direction="NEUTRAL",
                impact=0.28,
                explanation="Average service history neither strongly increases nor reduces risk.",
            )
        return InsightDriver(
            factor="Service history",
            observed_value=f"Score {service_score:.1f}/10",
            direction="RISK_DOWN",
            impact=0.72,
            explanation="Consistent service history lowers expected maintenance risk.",
        )

    @staticmethod
    def _service_recency_driver(days_since_service: float) -> InsightDriver:
        if days_since_service >= 240:
            return InsightDriver(
                factor="Service recency",
                observed_value=f"{days_since_service:.0f} days since last service",
                direction="RISK_UP",
                impact=0.78,
                explanation="Long intervals without service materially increase maintenance risk.",
            )
        if days_since_service >= 120:
            return InsightDriver(
                factor="Service recency",
                observed_value=f"{days_since_service:.0f} days since last service",
                direction="RISK_UP",
                impact=0.56,
                explanation="Service interval is extended and may elevate maintenance risk.",
            )
        return InsightDriver(
            factor="Service recency",
            observed_value=f"{days_since_service:.0f} days since last service",
            direction="RISK_DOWN",
            impact=0.44,
            explanation="Recent servicing is a protective signal for maintenance health.",
        )

    @staticmethod
    def _component_driver(factor: str, condition: str) -> InsightDriver:
        normalized = condition.strip().lower()
        if normalized in {"worn out", "worn", "poor", "bad"}:
            return InsightDriver(
                factor=factor,
                observed_value=condition,
                direction="RISK_UP",
                impact=0.68,
                explanation=f"{factor} is degraded, increasing mechanical failure risk.",
            )
        if normalized in {"new", "excellent"}:
            return InsightDriver(
                factor=factor,
                observed_value=condition,
                direction="RISK_DOWN",
                impact=0.46,
                explanation=f"{factor} is in strong condition and helps reduce near-term risk.",
            )
        return InsightDriver(
            factor=factor,
            observed_value=condition,
            direction="NEUTRAL",
            impact=0.24,
            explanation=f"{factor} is acceptable but should still be monitored routinely.",
        )

    @staticmethod
    def _battery_driver(status: str) -> InsightDriver:
        normalized = status.strip().lower()
        if normalized in {"weak", "low", "degraded", "poor"}:
            return InsightDriver(
                factor="Battery status",
                observed_value=status,
                direction="RISK_UP",
                impact=0.62,
                explanation="Weak battery health increases breakdown probability and secondary faults.",
            )
        if normalized in {"new", "fresh"}:
            return InsightDriver(
                factor="Battery status",
                observed_value=status,
                direction="RISK_DOWN",
                impact=0.4,
                explanation="Strong battery health reduces electrical-failure risk.",
            )
        return InsightDriver(
            factor="Battery status",
            observed_value=status,
            direction="NEUTRAL",
            impact=0.22,
            explanation="Battery status is acceptable; regular checks are still advised.",
        )

    @staticmethod
    def _accident_driver(accident_history: float) -> InsightDriver:
        if accident_history >= 2:
            return InsightDriver(
                factor="Accident history",
                observed_value=f"{accident_history:.0f} incidents",
                direction="RISK_UP",
                impact=0.74,
                explanation="Multiple accidents can increase hidden wear and maintenance complexity.",
            )
        if accident_history > 0:
            return InsightDriver(
                factor="Accident history",
                observed_value=f"{accident_history:.0f} incidents",
                direction="RISK_UP",
                impact=0.48,
                explanation="Past accidents add moderate uncertainty to component reliability.",
            )
        return InsightDriver(
            factor="Accident history",
            observed_value="No incidents",
            direction="RISK_DOWN",
            impact=0.33,
            explanation="No accident history is a modestly protective maintenance signal.",
        )

    @staticmethod
    def _mileage_driver(mileage: float) -> InsightDriver:
        if mileage >= 250000:
            return InsightDriver(
                factor="Mileage",
                observed_value=f"{mileage:,.0f} km",
                direction="RISK_UP",
                impact=0.64,
                explanation="Very high mileage increases cumulative wear and long-term failure likelihood.",
            )
        if mileage >= 120000:
            return InsightDriver(
                factor="Mileage",
                observed_value=f"{mileage:,.0f} km",
                direction="RISK_UP",
                impact=0.46,
                explanation="Higher mileage adds moderate wear-related maintenance risk.",
            )
        return InsightDriver(
            factor="Mileage",
            observed_value=f"{mileage:,.0f} km",
            direction="RISK_DOWN",
            impact=0.28,
            explanation="Mileage is within a lower-wear band for typical fleet operation.",
        )

    @staticmethod
    def _usage_driver(owner_type: str) -> InsightDriver:
        if owner_type.strip().lower() == "commercial":
            return InsightDriver(
                factor="Usage profile",
                observed_value="Commercial/heavy-duty",
                direction="RISK_UP",
                impact=0.44,
                explanation="Commercial usage tends to increase duty cycle and component stress.",
            )
        return InsightDriver(
            factor="Usage profile",
            observed_value="Individual/light-duty",
            direction="RISK_DOWN",
            impact=0.3,
            explanation="Lighter duty cycles typically reduce maintenance burden.",
        )

    @staticmethod
    def _data_quality_warnings(
        *,
        mileage: float,
        engine_hours: float,
        reported_issues: float,
    ) -> list[str]:
        warnings: list[str] = []
        if mileage > 1_500_000:
            warnings.append(
                "Mileage is extremely high and likely outside normal training range; treat the prediction as lower reliability."
            )
        if engine_hours > 0 and mileage / engine_hours > 2500:
            warnings.append(
                "Mileage-to-engine-hours ratio is unusually high; verify telemetry inputs for unit consistency."
            )
        if reported_issues >= 15:
            warnings.append(
                "Very high number of active fault codes detected; immediate workshop inspection is recommended."
            )
        return warnings

    @staticmethod
    def _recommendations_from_drivers(
        drivers: list[InsightDriver],
        risk_level: str,
    ) -> list[RecommendationItem]:
        recommendations: list[RecommendationItem] = []
        for driver in drivers:
            factor = driver.factor.lower()
            observed = driver.observed_value.lower()
            if factor == "reported issues" and driver.direction == "RISK_UP":
                recommendations.append(
                    RecommendationItem(
                        priority="HIGH",
                        action="Run full diagnostic scan and resolve active fault codes.",
                        rationale="Active fault codes are one of the strongest maintenance risk drivers.",
                    )
                )
            if factor == "service recency" and driver.direction == "RISK_UP":
                recommendations.append(
                    RecommendationItem(
                        priority="HIGH" if risk_level == "HIGH" else "MEDIUM",
                        action="Schedule preventive service within 7 days.",
                        rationale="Extended service intervals increase probability of avoidable failures.",
                    )
                )
            if factor in {"brake condition", "tire condition", "battery status"} and driver.direction == "RISK_UP":
                recommendations.append(
                    RecommendationItem(
                        priority="MEDIUM",
                        action=f"Inspect and service {factor} immediately.",
                        rationale="Component health indicators suggest rising failure risk.",
                    )
                )
            if factor == "service history" and driver.direction == "RISK_UP":
                recommendations.append(
                    RecommendationItem(
                        priority="MEDIUM",
                        action="Move to shorter maintenance intervals and enforce service logs.",
                        rationale="Irregular service patterns correlate with elevated maintenance incidents.",
                    )
                )
            if factor == "mileage" and "km" in observed and driver.direction == "RISK_UP":
                recommendations.append(
                    RecommendationItem(
                        priority="LOW",
                        action="Increase preventive inspection frequency for wear-prone components.",
                        rationale="High cumulative mileage increases wear even if current risk is not critical.",
                    )
                )

        if not recommendations:
            recommendations.append(
                RecommendationItem(
                    priority="LOW",
                    action="Maintain current service schedule and continue monitoring fault codes.",
                    rationale="Current indicators do not show immediate high-risk maintenance pressure.",
                )
            )

        deduped: list[RecommendationItem] = []
        seen: set[str] = set()
        for item in recommendations:
            key = item.action
            if key in seen:
                continue
            seen.add(key)
            deduped.append(item)
        return deduped[:5]

    @staticmethod
    def _merge_llm_recommendations(
        *,
        existing: list[RecommendationItem],
        llm_recommendations: list[dict[str, str]],
        risk_level: str,
    ) -> list[RecommendationItem]:
        merged = list(existing)
        default_priority = "HIGH" if risk_level == "HIGH" else "MEDIUM"
        if risk_level == "LOW":
            default_priority = "LOW"

        for llm_item in llm_recommendations:
            action = llm_item.get("action", "").strip()
            rationale = llm_item.get("rationale", "").strip()
            if not action or not rationale:
                continue
            merged.insert(
                0,
                RecommendationItem(
                    priority=default_priority,
                    action=action,
                    rationale=rationale,
                ),
            )

        deduped: list[RecommendationItem] = []
        seen: set[str] = set()
        for item in merged:
            key = item.action.lower()
            if key in seen:
                continue
            seen.add(key)
            deduped.append(item)
        return deduped[:5]

    @staticmethod
    def _build_insight_summary(
        *,
        probability: float,
        risk_level: str,
        drivers: list[InsightDriver],
    ) -> str:
        top_risk = [driver.factor for driver in drivers if driver.direction == "RISK_UP"][:2]
        top_protective = [driver.factor for driver in drivers if driver.direction == "RISK_DOWN"][:2]

        risk_text = f"Estimated failure-risk probability is {probability * 100:.2f}% ({risk_level})."
        if top_risk and top_protective:
            return (
                f"{risk_text} Main upward drivers: {', '.join(top_risk)}. "
                f"Main stabilizers: {', '.join(top_protective)}."
            )
        if top_risk:
            return f"{risk_text} Main upward drivers: {', '.join(top_risk)}."
        if top_protective:
            return f"{risk_text} Main stabilizers: {', '.join(top_protective)}."
        return risk_text

    def _normalize_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        normalized: dict[str, Any] = {}
        for key, value in payload.items():
            normalized[self._normalize_key(str(key))] = value

        # Keep compatibility with pydantic validation if caller passes strongly typed object.
        validated = VehicleInput(**normalized).model_dump()
        return {
            k: v
            for k, v in validated.items()
            if v is not None
        }

    @staticmethod
    def _pick(payload: dict[str, Any], *keys: str) -> Any:
        for key in keys:
            if key in payload and payload[key] not in (None, ""):
                return payload[key]
        return None

    def _extract_feature_importance(self) -> dict[str, float]:
        model = self.pipeline.named_steps.get("model")
        preprocessor = self.pipeline.named_steps.get("preprocessor")
        if model is None or preprocessor is None:
            return {}

        expanded_names = self._expanded_feature_names(preprocessor)
        if not expanded_names:
            return {}

        raw_importance: np.ndarray | None = None
        if hasattr(model, "feature_importances_"):
            raw_importance = np.asarray(model.feature_importances_, dtype=float)
        elif hasattr(model, "coef_"):
            coef = np.asarray(model.coef_, dtype=float)
            raw_importance = np.abs(coef[0] if coef.ndim > 1 else coef)

        if raw_importance is None or raw_importance.shape[0] != len(expanded_names):
            return {}

        cat_features = self._categorical_feature_names(preprocessor)
        grouped: dict[str, float] = {}
        for feature_name, value in zip(expanded_names, raw_importance):
            base = self._base_feature_name(feature_name, cat_features)
            grouped[base] = grouped.get(base, 0.0) + float(value)

        total = sum(grouped.values()) or 1.0
        ordered = sorted(grouped.items(), key=lambda item: item[1], reverse=True)
        top_10 = ordered[:10]
        return {
            self._normalize_key(name): round(value / total, 4)
            for name, value in top_10
        }

    @staticmethod
    def _categorical_feature_names(preprocessor: Any) -> list[str]:
        transformers = getattr(preprocessor, "transformers_", None)
        if not transformers:
            return []
        for name, _, features in transformers:
            if name == "cat":
                return list(features)
        return []

    @staticmethod
    def _expanded_feature_names(preprocessor: Any) -> list[str]:
        transformers = getattr(preprocessor, "transformers_", None)
        if not transformers:
            return []

        numeric: list[str] = []
        categorical_raw: list[str] = []
        for name, _, features in transformers:
            if name == "num":
                numeric = list(features)
            elif name == "cat":
                categorical_raw = list(features)

        cat_transformer = preprocessor.named_transformers_.get("cat")
        categorical: list[str] = []
        if cat_transformer is not None and hasattr(cat_transformer, "get_feature_names_out"):
            categorical = list(cat_transformer.get_feature_names_out(categorical_raw))

        return numeric + categorical

    @staticmethod
    def _base_feature_name(expanded_name: str, categorical_features: list[str]) -> str:
        for feature in categorical_features:
            prefix = f"{feature}_"
            if expanded_name.startswith(prefix):
                return feature
        return expanded_name


@lru_cache(maxsize=1)
def get_prediction_service() -> PredictionService:
    return PredictionService()
