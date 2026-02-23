# FleetAI - Vehicle Maintenance Prediction System (Milestone-1)

Milestone-1 delivers a complete prediction workflow:

- FastAPI backend with sklearn pipeline inference
- Next.js frontend with manual and CSV prediction flows
- Risk classification (`LOW | MEDIUM | HIGH`)
- Confidence and risk probability
- Global model feature importance
- Row-level meaningful insight (drivers, recommendations, warnings)

## System Architecture

```text
frontend (Next.js)  --->  backend (FastAPI /predict)
                           |
                           ---> model/vehicle_maintenance_pipeline.pkl
```

## What Is "Meaningful Insight" In This Build

Prediction responses now include both model output and an operational explanation:

- `risk_probability`: model probability of HIGH-risk class
- `confidence`: `max(probability, 1 - probability)`
- `insight_summary`: short interpretation sentence
- `insight_drivers[]`: row-specific factors with direction (`RISK_UP`, `RISK_DOWN`, `NEUTRAL`) and impact score
- `recommendations[]`: actionable maintenance steps with priority
- `data_warnings[]`: suspicious input warnings (for out-of-range telemetry)
- `insight_source`: `RULES` or `GENAI_LLM`

GenAI path:

- If `ENABLE_LLM_INSIGHTS=true` and `GOOGLE_API_KEY` is set, LangChain + Google GenAI augments summary/recommendations.
- If not configured, the API safely falls back to deterministic rule-based insights.

Important distinction:

- `feature_importance` is **global model weight** (model-wide)
- `insight_drivers` is **row-specific operational interpretation**

## Repository Structure

```text
backend/
  app/
    api/predict.py
    services/prediction_service.py
    schemas/prediction.py
    models/prediction_record.py
    main.py
  tests/
  requirements.txt
frontend/
  src/app/predict/page.tsx
  src/services/predictionService.ts
  src/types/prediction.ts
model/
  vehicle_maintenance_pipeline.pkl
api/
  index.py                 # Vercel backend entrypoint
vercel.json                # Vercel backend routing
requirements.txt           # Vercel backend deps
```

## Local Development

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
PYTHONPATH=backend uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend
npm install
echo "NEXT_PUBLIC_API_BASE_URL=http://localhost:8000" > .env.local
npm run dev
```

Open:

- `http://localhost:3000`
- `http://localhost:3000/predict`

## API Contract

### `POST /predict` (JSON)

Request:

```json
{
  "mileage": 64000,
  "engine_hours": 1200,
  "fault_codes": "P0171,P0420",
  "service_history": "average",
  "usage_patterns": "mixed city driving"
}
```

Response shape:

```json
{
  "risk_level": "LOW",
  "risk_probability": 0.1751,
  "confidence": 0.8249,
  "feature_importance": {
    "reported_issues": 0.3051
  },
  "insight_summary": "Estimated failure-risk probability is ...",
  "insight_drivers": [
    {
      "factor": "Reported issues",
      "observed_value": "1 active fault code",
      "direction": "RISK_UP",
      "impact": 0.42,
      "explanation": "..."
    }
  ],
  "recommendations": [
    {
      "priority": "MEDIUM",
      "action": "Run full diagnostic scan and resolve active fault codes.",
      "rationale": "..."
    }
  ],
  "data_warnings": [],
  "total_records": 1,
  "predictions": null,
  "metadata": null
}
```

### `POST /predict` (CSV)

Multipart field:

- `file`: CSV

Required columns:

- `mileage`
- `engine_hours`
- `fault_codes`
- `service_history`
- `usage_patterns`

For batch requests, response includes `predictions[]` and a top-level summary of the highest-risk row.

## Risk Thresholds

- `LOW`: probability `< 0.30`
- `MEDIUM`: `0.30 <= probability < 0.70`
- `HIGH`: probability `>= 0.70`

## Tests

```bash
PYTHONPATH=backend pytest -q backend/tests
```

## Deploy To Vercel (Frontend + Backend)

Use **two Vercel projects** in the same repo.

### 1) Backend project (FastAPI + model)

- Vercel project root: repository root (`/`)
- Uses:
  - `api/index.py`
  - `vercel.json`
  - `requirements.txt`
  - `model/vehicle_maintenance_pipeline.pkl`

Deploy:

```bash
vercel --prod
```

Optional GenAI env vars on backend project:

```text
ENABLE_LLM_INSIGHTS=true
GOOGLE_API_KEY=<your-key>
GENAI_MODEL=gemini-1.5-flash
```

After deploy, verify:

- `https://<backend-domain>/health`
- `https://<backend-domain>/docs`

### 2) Frontend project (Next.js)

- Vercel project root: `frontend/`
- Set env var:
  - `NEXT_PUBLIC_API_BASE_URL=https://<backend-domain>`

Deploy:

```bash
cd frontend
vercel --prod
```

### Why this setup

- Backend project must include `model/vehicle_maintenance_pipeline.pkl` from repo root.
- Frontend project remains a standard Next.js deployment and calls backend via env-configured URL.

## Notes

- Model is loaded once per runtime instance via cached prediction service.
- Feature importance is global model behavior; row-level interpretation is in `insight_drivers`.
