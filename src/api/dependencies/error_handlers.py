from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.api.dependencies.request_context import CORRELATION_HEADER, get_correlation_id
from src.core.errors import (
    DEPENDENCY_TEMPORARILY_UNAVAILABLE,
    IDEMPOTENCY_KEY_CONFLICT,
    INVOICE_DUPLICATE_REFERENCE,
    INVOICE_INVALID_STATE,
    INVOICE_NOT_FOUND,
    INVOICE_VENDOR_PO_MISMATCH,
    PURCHASE_ORDER_INVALID_STATE,
    PURCHASE_ORDER_LINE_INVALID,
    PURCHASE_ORDER_NOT_FOUND,
    PURCHASE_ORDER_OVER_RECEIPT,
    VENDOR_INACTIVE,
    VENDOR_NOT_FOUND,
    ServiceError,
    dependency_temporarily_unavailable,
)


ERROR_STATUS_BY_CODE = {
    VENDOR_NOT_FOUND: 404,
    VENDOR_INACTIVE: 409,
    IDEMPOTENCY_KEY_CONFLICT: 409,
    PURCHASE_ORDER_NOT_FOUND: 404,
    PURCHASE_ORDER_INVALID_STATE: 409,
    PURCHASE_ORDER_LINE_INVALID: 422,
    PURCHASE_ORDER_OVER_RECEIPT: 409,
    INVOICE_NOT_FOUND: 404,
    INVOICE_DUPLICATE_REFERENCE: 409,
    INVOICE_VENDOR_PO_MISMATCH: 409,
    INVOICE_INVALID_STATE: 409,
    DEPENDENCY_TEMPORARILY_UNAVAILABLE: 503,
}


def error_to_response(request: Request, error: ServiceError) -> JSONResponse:
    correlation_id = get_correlation_id(request)
    status_code = ERROR_STATUS_BY_CODE.get(error.code, 500)
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": error.code,
                "category": error.category,
                "retryable": error.retryable,
                "message": error.message,
                "correlation_id": correlation_id,
            }
        },
        headers={CORRELATION_HEADER: correlation_id},
    )


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, _: Exception) -> JSONResponse:
        return error_to_response(request, dependency_temporarily_unavailable())
