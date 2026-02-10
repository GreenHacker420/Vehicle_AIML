# Backend - FleetAI Milestone-1

FastAPI inference backend for vehicle maintenance risk prediction.

## Start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
PYTHONPATH=backend uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Endpoints

- `GET /health`
- `POST /predict`

`POST /predict` supports:

- JSON payloads
- CSV upload (`multipart/form-data`, field name `file`)

## Core Files

- `app/api/predict.py`
- `app/services/prediction_service.py`
- `app/schemas/prediction.py`
- `app/main.py`

## Tests

```bash
source .venv/bin/activate
PYTHONPATH=backend pytest -q backend/tests
```

