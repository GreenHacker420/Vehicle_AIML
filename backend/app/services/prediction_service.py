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

from app.config import settings
from app.schemas.prediction import PredictionItem, PredictionResponse, VehicleInput


class PredictionService:
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
        self.model_path = model_path or settings.model_path
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

        item = PredictionItem(
            risk_level=self._map_risk_level(probability),
            confidence=round(self._confidence(probability), 4),
            feature_importance=self._feature_importance,
        )
        return PredictionResponse(**item.model_dump())

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
            PredictionItem(
                risk_level=self._map_risk_level(float(probability)),
                confidence=round(self._confidence(float(probability)), 4),
                feature_importance=self._feature_importance,
            )
            for probability in probabilities
        ]


        summary = max(
            prediction_items,
            key=lambda item: (self._risk_rank(item.risk_level), item.confidence),
        )

        return PredictionResponse(
            risk_level=summary.risk_level,
            confidence=summary.confidence,
            feature_importance=summary.feature_importance,
            total_records=len(prediction_items),
            predictions=prediction_items,
            metadata={"summary_strategy": "highest_risk"},
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

    def _normalize_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        normalized: dict[str, Any] = {}
        for key, value in payload.items():
            normalized[self._normalize_key(str(key))] = value

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

