# Backend - FleetAI

FastAPI backend for vehicle maintenance risk prediction and fleet management.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
PYTHONPATH=backend uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Endpoints

- `GET /health` — service health check
- `POST /predict` — predict maintenance risk (JSON or CSV upload)
- `POST /vehicles` — register a new vehicle
- `GET /vehicles` — list all registered vehicles
- `GET /vehicles/{id}` — get a specific vehicle

## Configuration

Environment variables (prefixed with `FLEET_`):

| Variable | Default | Description |
|---|---|---|
| `FLEET_MODEL_PATH` | `model/vehicle_maintenance_pipeline.pkl` | Path to trained model |
| `FLEET_CORS_ORIGINS` | `["*"]` | Allowed CORS origins |
| `FLEET_DEBUG` | `false` | Enable debug logging |

## Tests

```bash
PYTHONPATH=backend pytest -q backend/tests
```

## Project Structure

```
app/
  api/
    predict.py
    vehicles.py
  models/
    prediction_record.py
    vehicle.py
  schemas/
    prediction.py
    vehicle.py
  services/
    prediction_service.py
  config.py
  errors.py
  logging_config.py
  main.py
tests/
  conftest.py
  test_batch_predict.py
  test_health.py
  test_predict.py
  test_predict_contract.py
  test_risk_mapping.py
  test_validation.py
  test_vehicles.py
  fixtures/
    valid_sample.csv
    invalid_rows.csv
```
