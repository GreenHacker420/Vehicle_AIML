from __future__ import annotations


def test_predict_json_contract_shape(client) -> None:
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

    assert set(
        [
            "risk_level",
            "risk_probability",
            "confidence",
            "feature_importance",
            "insight_summary",
            "insight_source",
            "insight_drivers",
            "recommendations",
            "data_warnings",
        ]
    ).issubset(payload)
    assert payload["risk_level"] in {"LOW", "MEDIUM", "HIGH"}
    assert 0 <= payload["risk_probability"] <= 1
    assert isinstance(payload["feature_importance"], dict)

