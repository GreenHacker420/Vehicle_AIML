from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status

from app.schemas.prediction import PredictionResponse
from app.services.prediction_service import PredictionService, get_prediction_service

router = APIRouter()


@router.post("/predict", response_model=PredictionResponse)
async def predict(
    request: Request,
    file: UploadFile | None = File(default=None),
    service: PredictionService = Depends(get_prediction_service),
) -> PredictionResponse:
    if file is not None:
        rows = await service.parse_csv_upload(file)
        return service.predict_many(rows)

    try:
        body = await request.json()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Request body must be valid JSON or multipart CSV upload.",
        ) from exc

    payload_items = _unwrap_payload(body)
    if isinstance(payload_items, list):
        return service.predict_many(payload_items)
    return service.predict_single(payload_items)


def _unwrap_payload(body: Any) -> dict[str, Any] | list[dict[str, Any]]:
    if isinstance(body, list):
        return [_ensure_dict(item) for item in body]
    if not isinstance(body, dict):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="JSON payload must be an object or an array of objects.",
        )

    if "vehicle_data" in body:
        payload = body["vehicle_data"]
        if isinstance(payload, list):
            return [_ensure_dict(item) for item in payload]
        return _ensure_dict(payload)

    if "vehicles" in body:
        payload = body["vehicles"]
        if not isinstance(payload, list):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="`vehicles` must be an array of objects.",
            )
        return [_ensure_dict(item) for item in payload]

    return _ensure_dict(body)


def _ensure_dict(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Prediction input rows must be JSON objects.",
        )
    return payload

