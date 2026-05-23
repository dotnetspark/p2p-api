from __future__ import annotations

from dataclasses import dataclass

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.api.dependencies.request_context import CORRELATION_HEADER, get_correlation_id


@dataclass
class AppError(Exception):
    code: str
    message: str
    status_code: int
    category: str
    retryable: bool = False


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        correlation_id = get_correlation_id(request)
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.code,
                    "category": exc.category,
                    "retryable": exc.retryable,
                    "message": exc.message,
                    "correlation_id": correlation_id,
                }
            },
            headers={CORRELATION_HEADER: correlation_id},
        )

    @app.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, _: Exception) -> JSONResponse:
        correlation_id = get_correlation_id(request)
        return JSONResponse(
            status_code=503,
            content={
                "error": {
                    "code": "DEPENDENCY_TEMPORARILY_UNAVAILABLE",
                    "category": "infrastructure",
                    "retryable": True,
                    "message": "A temporary dependency failure prevented request completion.",
                    "correlation_id": correlation_id,
                }
            },
            headers={CORRELATION_HEADER: correlation_id},
        )
