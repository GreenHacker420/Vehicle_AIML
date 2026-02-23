# Backend - FleetAI Milestone-1

FastAPI inference backend for vehicle maintenance risk prediction.

## Run Locally

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

- JSON payloads (single or array)
- CSV upload (`multipart/form-data`, field `file`)

## Response fields (highlights)

- `risk_level`
- `risk_probability`
- `confidence`
- `feature_importance` (global model weight)
- `insight_summary`
- `insight_source` (`RULES` or `GENAI_LLM`)
- `insight_drivers`
- `recommendations`
- `data_warnings`

## Tests

```bash
PYTHONPATH=backend pytest -q backend/tests
```

## Deploy Backend To Vercel

Deploy from repository root so the model file is bundled:

- `model/vehicle_maintenance_pipeline.pkl`
- `api/index.py`
- `vercel.json`
- root `requirements.txt`

```bash
cd /path/to/repo-root
vercel --prod
```

Health check:

```bash
curl https://<backend-domain>/health
```

Optional GenAI enrichment:

```text
ENABLE_LLM_INSIGHTS=true
GOOGLE_API_KEY=<your-key>
GENAI_MODEL=gemini-1.5-flash
```

If these vars are not set, the backend returns deterministic rule-based insights.
