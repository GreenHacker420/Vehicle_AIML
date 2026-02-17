from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_predict_json_contract_shape() -> None:
    response = client.post(
        "/predict",
        json={
            "mileage": 54000,
            "engine_hours": 1100,
            "fault_codes": "P0171",
            "service_history": "average",
            "usage_patterns": "mixed city driving",
        },
    )

    assert response.status_code == 200
    payload = response.json()

    assert set(["risk_level", "confidence", "feature_importance"]).issubset(payload)
    assert payload["risk_level"] in {"LOW", "MEDIUM", "HIGH"}
    assert isinstance(payload["feature_importance"], dict)
