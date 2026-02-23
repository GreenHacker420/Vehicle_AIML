from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.predict import router as predict_router
from app.api.vehicles import router as vehicles_router
from app.config import settings
from app.errors import generic_error_handler, value_error_handler
from app.services.prediction_service import get_prediction_service


@asynccontextmanager
async def lifespan(_: FastAPI):
    get_prediction_service()
    yield


app = FastAPI(
    title="Vehicle Maintenance Prediction API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(predict_router)
app.include_router(vehicles_router)

app.add_exception_handler(ValueError, value_error_handler)
app.add_exception_handler(Exception, generic_error_handler)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}

