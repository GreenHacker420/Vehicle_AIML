from __future__ import annotations

import logging

from fastapi import Request, status
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


async def value_error_handler(_request: Request, exc: ValueError) -> JSONResponse:
    """Return 422 for any unhandled ValueError raised during request handling."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": str(exc)},
    )


async def generic_error_handler(_request: Request, exc: Exception) -> JSONResponse:
    """Catch-all handler — logs the traceback and returns a generic 500."""
    logger.exception("unhandled error during request")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "internal server error"},
    )
