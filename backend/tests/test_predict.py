from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_predict_json_with_milestone_fields() -> None:
    response = client.post(
        "/predict",
        json={
            "mileage": 64000,
            "engine_hours": 1200,
            "fault_codes": "P0171,P0420",
            "service_history": "average",
            "usage_patterns": "mixed city driving",
        },
    )

    assert response.status_code == 200
    body = response.json()

    assert body["risk_level"] in {"LOW", "MEDIUM", "HIGH"}
    assert 0 <= body["risk_probability"] <= 1
    assert 0 <= body["confidence"] <= 1
    assert isinstance(body["feature_importance"], dict)
    assert len(body["feature_importance"]) > 0
    assert isinstance(body["insight_summary"], str)
    assert len(body["insight_drivers"]) > 0
    assert isinstance(body["recommendations"], list)


def test_predict_csv_upload() -> None:
    csv_data = "\n".join(
        [
            "mileage,engine_hours,fault_codes,service_history,usage_patterns",
            "42000,900,P0100;P0110,good,normal mixed",
            "157000,5500,P0420|P0430|P0300,poor,heavy commercial city use",
        ]
    )

    response = client.post(
        "/predict",
        files={"file": ("vehicles.csv", csv_data, "text/csv")},
    )

    assert response.status_code == 200
    body = response.json()

    assert body["total_records"] == 2
    assert body["risk_level"] in {"LOW", "MEDIUM", "HIGH"}
    assert 0 <= body["risk_probability"] <= 1
    assert body["predictions"] is not None
    assert len(body["predictions"]) == 2
    assert all("insight_drivers" in item for item in body["predictions"])
