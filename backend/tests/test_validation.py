from __future__ import annotations

from pathlib import Path

FIXTURES = Path(__file__).parent / "fixtures"


def test_non_csv_upload_rejected(client) -> None:
    response = client.post(
        "/predict",
        files={"file": ("data.txt", "some random text", "text/plain")},
    )
    assert response.status_code == 400


def test_empty_csv_upload_rejected(client) -> None:
    response = client.post(
        "/predict",
        files={"file": ("empty.csv", "", "text/csv")},
    )
    assert response.status_code == 400


def test_invalid_json_body_rejected(client) -> None:
    response = client.post(
        "/predict",
        content="this is not json",
        headers={"content-type": "application/json"},
    )
    assert response.status_code == 400


def test_missing_fields_rejected(client) -> None:
    response = client.post(
        "/predict",
        json={"unrelated_key": "value"},
    )
    assert response.status_code == 422
