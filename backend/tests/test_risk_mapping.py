from __future__ import annotations

from app.services.prediction_service import PredictionService


def test_risk_mapping_thresholds() -> None:
    assert PredictionService._map_risk_level(0.05) == "LOW"
    assert PredictionService._map_risk_level(0.30) == "MEDIUM"
    assert PredictionService._map_risk_level(0.69) == "MEDIUM"
    assert PredictionService._map_risk_level(0.70) == "HIGH"


def test_confidence_bounds() -> None:
    assert 0.5 <= PredictionService._confidence(0.1) <= 1.0
    assert 0.5 <= PredictionService._confidence(0.9) <= 1.0


def test_data_warning_for_extreme_mileage() -> None:
    service = PredictionService()
    response = service.predict_single(
        {
            "mileage": 9_000_000,
            "engine_hours": 1200,
            "fault_codes": "P0171",
            "service_history": "good",
            "usage_patterns": "heavy commercial",
        }
    )

    assert any("outside normal training range" in warning for warning in response.data_warnings)
