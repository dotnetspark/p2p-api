from __future__ import annotations

from fastapi import APIRouter, Depends, Header, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from src.api.dependencies.error_handlers import error_to_response
from src.api.schemas.invoice import (
    CreateInvoiceRequest,
    InvoiceApprovalResponse,
    InvoiceMatchResponse,
    InvoicePaymentResponse,
    InvoiceResponse,
)
from src.domain.services.invoice_approval_service import InvoiceApprovalService
from src.domain.services.invoice_matching_service import InvoiceMatchingService
from src.domain.services.invoice_payment_service import InvoicePaymentService
from src.domain.services.invoice_service import InvoiceService
from src.persistence.database import get_db_session


router = APIRouter()


@router.post("/invoices", response_model=InvoiceResponse, status_code=201)
def create_invoice(
    payload: CreateInvoiceRequest,
    request: Request,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    session: Session = Depends(get_db_session),
) -> InvoiceResponse | JSONResponse:
    result = InvoiceService().create_invoice(
        session=session,
        vendor_id=payload.vendor_id,
        purchase_order_id=payload.purchase_order_id,
        invoice_number=payload.invoice_number,
        invoice_amount=payload.invoice_amount,
        idempotency_key=idempotency_key,
    )
    if result.error is not None:
        return error_to_response(request, result.error)
    return InvoiceResponse.from_domain(result.value)


@router.post("/invoices/{invoice_id}/match", response_model=InvoiceMatchResponse)
def match_invoice(
    invoice_id: str,
    request: Request,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    session: Session = Depends(get_db_session),
) -> InvoiceMatchResponse | JSONResponse:
    result = InvoiceMatchingService().match_invoice(
        session=session,
        invoice_id=invoice_id,
        idempotency_key=idempotency_key,
    )
    if result.error is not None:
        return error_to_response(request, result.error)
    body = InvoiceMatchResponse.from_domain(result.value)
    return JSONResponse(status_code=result.value.http_status_code, content=body.model_dump(mode="json", exclude_none=True))


@router.post("/invoices/{invoice_id}/approve", response_model=InvoiceApprovalResponse)
def approve_invoice(
    invoice_id: str,
    request: Request,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    session: Session = Depends(get_db_session),
) -> InvoiceApprovalResponse | JSONResponse:
    result = InvoiceApprovalService().approve_invoice(
        session=session,
        invoice_id=invoice_id,
        idempotency_key=idempotency_key,
    )
    if result.error is not None:
        return error_to_response(request, result.error)
    return InvoiceApprovalResponse.from_domain(result.value)


@router.post("/invoices/{invoice_id}/pay", response_model=InvoicePaymentResponse)
def pay_invoice(
    invoice_id: str,
    request: Request,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    session: Session = Depends(get_db_session),
) -> InvoicePaymentResponse | JSONResponse:
    result = InvoicePaymentService().pay_invoice(
        session=session,
        invoice_id=invoice_id,
        idempotency_key=idempotency_key,
    )
    if result.error is not None:
        return error_to_response(request, result.error)
    return InvoicePaymentResponse.from_domain(result.value)