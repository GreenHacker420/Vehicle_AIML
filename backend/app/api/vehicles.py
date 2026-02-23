from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.schemas.vehicle import VehicleCreate, VehicleResponse

router = APIRouter(prefix="/vehicles", tags=["vehicles"])

_store: list[dict] = []
_counter = 0


@router.post("", response_model=VehicleResponse, status_code=status.HTTP_201_CREATED)
def create_vehicle(payload: VehicleCreate) -> VehicleResponse:
    global _counter
    _counter += 1

    from datetime import datetime, timezone

    record = {
        "id": _counter,
        "name": payload.name,
        "mileage": payload.mileage,
        "engine_hours": payload.engine_hours,
        "created_at": datetime.now(timezone.utc),
    }
    _store.append(record)
    return VehicleResponse(**record)


@router.get("", response_model=list[VehicleResponse])
def list_vehicles() -> list[VehicleResponse]:
    return [VehicleResponse(**v) for v in _store]


@router.get("/{vehicle_id}", response_model=VehicleResponse)
def get_vehicle(vehicle_id: int) -> VehicleResponse:
    for vehicle in _store:
        if vehicle["id"] == vehicle_id:
            return VehicleResponse(**vehicle)
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found")
