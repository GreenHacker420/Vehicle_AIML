from __future__ import annotations


def test_predict_with_vehicle_data_wrapper(client) -> None:
    response = client.post(
        "/predict",
        json={
            "vehicle_data": {
                "mileage": 72000,
                "engine_hours": 1400,
                "fault_codes": "P0300",
                "service_history": "good",
                "usage_patterns": "highway driving",
            }
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["risk_level"] in {"LOW", "MEDIUM", "HIGH"}


def test_predict_with_vehicles_array_wrapper(client) -> None:
    response = client.post(
        "/predict",
        json={
            "vehicles": [
                {
                    "mileage": 30000,
                    "engine_hours": 600,
                    "fault_codes": "P0100",
                    "service_history": "excellent",
                    "usage_patterns": "light suburban",
                },
                {
                    "mileage": 120000,
                    "engine_hours": 4000,
                    "fault_codes": "P0420,P0430",
                    "service_history": "poor",
                    "usage_patterns": "heavy commercial",
                },
            ]
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total_records"] == 2
    assert body["predictions"] is not None
    assert len(body["predictions"]) == 2


def test_predict_with_direct_array(client) -> None:
    response = client.post(
        "/predict",
        json=[
            {
                "mileage": 45000,
                "engine_hours": 800,
                "fault_codes": "none",
                "service_history": "average",
                "usage_patterns": "daily commute",
            }
        ],
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total_records"] == 1
