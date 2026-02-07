# FleetAI - Vehicle Maintenance Prediction System (Milestone-1)

Production-ready Milestone-1 implementation of a vehicle maintenance risk prediction flow with:

- FastAPI backend + scikit-learn pipeline inference
- Next.js App Router frontend (TypeScript)
- Manual input + CSV upload prediction modes
- Risk level, confidence score, and feature importance output

## What Was Completed

### Backend

- Added a clean FastAPI architecture:
  - `backend/app/api`
  - `backend/app/services`
  - `backend/app/models`
  - `backend/app/schemas`
- Implemented `POST /predict` supporting:
  - JSON payload
  - Multipart CSV upload (`file`)
- Added robust preprocessing/mapping from required milestone fields:
  - `mileage`, `engine_hours`, `fault_codes`, `service_history`, `usage_patterns`
- Added model singleton loading (loads once, cached)
- Added feature importance extraction from the trained pipeline
- Added tests for JSON + CSV paths

### Frontend

- Migrated app shell to TypeScript
- Added React Query for mutation-based prediction calls
- Built `/predict` with:
  - manual form
  - CSV drag/drop upload
  - loading/error/success states
  - risk level (color-coded), confidence, feature-importance table
- Upgraded UI with registry-installed components from:
  - React Bits
  - Aceternity UI
  - 21st.dev

## UI Component Sources

The frontend uses registry components installed via `shadcn`:

- Aceternity:
  - `src/components/ui/background-gradient.tsx`
  - `src/components/ui/hover-border-gradient.tsx`
  - `src/components/ui/input.tsx`
  - `src/components/ui/file-upload.tsx`
  - `src/components/ui/spotlight.tsx`
- React Bits:
  - `src/components/AnimatedContent.tsx`
  - `src/components/StarBorder.tsx`
- 21st.dev:
  - `src/components/ui/accordion.tsx`
  - `src/components/ui/table.tsx`
  - `src/components/ui/card.tsx`
  - `src/components/ui/badge.tsx`
  - `src/components/ui/textarea.tsx`

## Repository Structure

```text
backend/
  app/
    api/predict.py
    services/prediction_service.py
    schemas/prediction.py
    models/prediction_record.py
    main.py
  tests/test_predict.py
  requirements.txt
frontend/
  src/app/
    page.tsx
    predict/page.tsx
    layout.tsx
  src/components/
    ui/*
    AnimatedContent.tsx
    StarBorder.tsx
  src/providers/query-provider.tsx
  src/services/predictionService.ts
model/
  vehicle_maintenance_pipeline.pkl
```

## Prerequisites

- Python `3.11+` (tested with `3.13`)
- Node.js `20+` (tested with `v25`)
- npm `10+`

## Backend Setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Run API:

```bash
PYTHONPATH=backend uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Health check:

```bash
curl http://localhost:8000/health
```

## Frontend Setup

```bash
cd frontend
npm install
```

Create env file:

```bash
echo "NEXT_PUBLIC_API_BASE_URL=http://localhost:8000" > .env.local
```

Run frontend:

```bash
npm run dev
```

Open:

- `http://localhost:3000`
- Prediction page: `http://localhost:3000/predict`

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

Response:

```json
{
  "risk_level": "LOW",
  "confidence": 0.8587,
  "feature_importance": {
    "reported_issues": 0.3051
  },
  "total_records": 1,
  "predictions": null,
  "metadata": null
}
```

### `POST /predict` (CSV upload)

Multipart field:

- `file`: CSV

Required columns:

- `mileage`
- `engine_hours`
- `fault_codes`
- `service_history`
- `usage_patterns`

Batch mode returns `predictions[]` and `total_records`.

## Risk Thresholds

- `LOW`: probability `< 0.30`
- `MEDIUM`: `0.30 <= probability < 0.70`
- `HIGH`: probability `>= 0.70`

Confidence is `max(p, 1-p)`.

## Testing

Backend tests:

```bash
source backend/.venv/bin/activate
PYTHONPATH=backend pytest -q backend/tests
```

Frontend quality checks:

```bash
cd frontend
npm run lint
npm run build
```

## Performance

Model is loaded once at startup (singleton service cache). Inference is typically millisecond-level per request after warm-up and meets the `< 2s` milestone target.

## Notes

- The trained model artifact is read from:
  - `model/vehicle_maintenance_pipeline.pkl`
- The backend includes a Piccolo model (`PredictionRecord`) for clean architecture and future persistence extension.
