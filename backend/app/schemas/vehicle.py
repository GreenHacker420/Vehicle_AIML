from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class VehicleCreate(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    mileage: float = Field(ge=0)
    engine_hours: float = Field(ge=0)


class VehicleResponse(BaseModel):
    id: int
    name: str
    mileage: float
    engine_hours: float
    created_at: datetime
