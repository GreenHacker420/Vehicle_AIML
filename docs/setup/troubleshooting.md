# Local Setup Troubleshooting

## Backend not starting
- verify `backend/requirements.txt` is installed
- confirm model file exists at `model/vehicle_maintenance_pipeline.pkl`

## Frontend API calls failing
- confirm `NEXT_PUBLIC_API_BASE_URL` points to backend host
- check browser network tab for CORS or 4xx details

## CSV upload failing
- validate required columns and UTF-8 encoding
