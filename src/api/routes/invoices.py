from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, Header, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from src.api.dependencies.error_handlers import error_to_response
from src.api.dependencies.request_context import get_correlation_id
from src.api.schemas.invoice import (
    CreateInvoiceRequest,
    CreditCheckStatusResponse,
    InvoiceApprovalResponse,
    InvoiceMatchResponse,
    InvoicePaymentResponse,
    InvoiceResponse,
)
from src.domain.services.invoice_approval_service import InvoiceApprovalService
from src.domain.services.invoice_matching_service import InvoiceMatchingService
from src.domain.services.invoice_payment_service import InvoicePaymentService
from src.domain.services.invoice_service import InvoiceService
from src.domain.services.vendor_credit_alert_service import VendorCreditAlertService
from src.persistence.database import get_db_session


router = APIRouter()


@router.get("/credit-checks/{credit_check_id}", response_model=CreditCheckStatusResponse)
def get_credit_check(
    credit_check_id: str,
    request: Request,
    session: Session = Depends(get_db_session),
) -> CreditCheckStatusResponse | JSONResponse:
    result = VendorCreditAlertService().get_credit_check(session, credit_check_id)
    if result.error is not None:
        return error_to_response(request, result.error)
    return CreditCheckStatusResponse.from_domain(result.value)


@router.post("/invoices", response_model=InvoiceResponse, status_code=201)
def create_invoice(
    payload: CreateInvoiceRequest,
    request: Request,
    background_tasks: BackgroundTasks,
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
        correlation_id=get_correlation_id(request),
    )
    if result.error is not None:
        return error_to_response(request, result.error)
    if result.value.should_schedule_credit_check:
        background_tasks.add_task(
            VendorCreditAlertService().dispatch_pending_credit_check,
            result.value.credit_check_id,
        )
    return InvoiceResponse.from_domain(result.value.invoice, credit_check_id=result.value.credit_check_id)


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
    background_tasks: BackgroundTasks,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    session: Session = Depends(get_db_session),
) -> InvoiceApprovalResponse | JSONResponse:
    result = InvoiceApprovalService().approve_invoice(
        session=session,
        invoice_id=invoice_id,
        idempotency_key=idempotency_key,
        correlation_id=get_correlation_id(request),
    )
    if result.error is not None:
        return error_to_response(request, result.error)
    if result.value.should_schedule_credit_check:
        background_tasks.add_task(
            VendorCreditAlertService().dispatch_pending_credit_check,
            result.value.credit_check_id,
        )
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