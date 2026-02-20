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
