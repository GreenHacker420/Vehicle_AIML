from __future__ import annotations


def test_create_vehicle(client) -> None:
    response = client.post(
        "/vehicles",
        json={"name": "Toyota Camry", "mileage": 45000, "engine_hours": 900},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Toyota Camry"
    assert body["mileage"] == 45000
    assert "id" in body
    assert "created_at" in body


def test_list_vehicles(client) -> None:
    client.post(
        "/vehicles",
        json={"name": "Honda Civic", "mileage": 30000, "engine_hours": 600},
    )
    response = client.get("/vehicles")
    assert response.status_code == 200
    vehicles = response.json()
    assert isinstance(vehicles, list)
    assert len(vehicles) >= 1


def test_get_vehicle_not_found(client) -> None:
    response = client.get("/vehicles/99999")
    assert response.status_code == 404


def test_create_vehicle_invalid_mileage(client) -> None:
    response = client.post(
        "/vehicles",
        json={"name": "Test Car", "mileage": -100, "engine_hours": 500},
    )
    assert response.status_code == 422
