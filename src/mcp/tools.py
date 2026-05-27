from __future__ import annotations

import json
from contextlib import contextmanager
from decimal import Decimal
from typing import Annotated, Callable, Iterator
from uuid import uuid4

from mcp.types import CallToolResult, TextContent
from sqlalchemy.orm import Session

from src.api.dependencies.error_handlers import ERROR_STATUS_BY_CODE
from src.api.schemas.invoice import (
    CreditCheckStatusResponse,
    InvoiceApprovalResponse,
    InvoiceMatchResponse,
    InvoicePaymentResponse,
    InvoiceResponse,
)
from src.api.schemas.purchase_order import GoodsReceiptLineInputRequest, PurchaseOrderLineInputRequest, PurchaseOrderResponse
from src.api.schemas.vendor_eligibility import VendorEligibilityResponse
from src.api.schemas.vendor_exposure import VendorExposureResponse
from src.core.errors import ServiceError
from src.core.results import Result
from src.domain.models.goods_receipt import GoodsReceiptLineInput
from src.domain.models.purchase_order import PurchaseOrderLineInput
from src.domain.services.goods_receipt_service import GoodsReceiptService
from src.domain.services.invoice_approval_service import InvoiceApprovalService
from src.domain.services.invoice_matching_service import InvoiceMatchingService
from src.domain.services.invoice_payment_service import InvoicePaymentService
from src.domain.services.invoice_service import InvoiceService
from src.domain.services.purchase_order_service import PurchaseOrderService
from src.domain.services.vendor_credit_alert_service import VendorCreditAlertService
from src.domain.services.vendor_eligibility_service import VendorEligibilityService
from src.domain.services.vendor_exposure_service import VendorExposureService
from src.mcp.models import (
    CreateInvoiceToolPayload,
    CreditCheckToolEnvelope,
    InvoiceApprovalToolEnvelope,
    InvoiceMatchToolEnvelope,
    InvoicePaymentToolEnvelope,
    InvoiceToolEnvelope,
    PurchaseOrderToolEnvelope,
    ToolEnvelope,
    ToolErrorPayload,
    VendorEligibilityToolEnvelope,
    VendorExposureToolEnvelope,
)
from src.persistence.database import get_session_factory


ToolResultText = TextContent


@contextmanager
def session_context() -> Iterator[Session]:
    session = get_session_factory()()
    try:
        yield session
    finally:
        session.close()


def resolve_correlation_id(correlation_id: str | None) -> str:
    return correlation_id or str(uuid4())


def tool_result_from_envelope(envelope: ToolEnvelope, *, is_error: bool = False) -> CallToolResult:
    structured_content = envelope.model_dump(mode="json", exclude_none=True)
    return CallToolResult(
        content=[TextContent(type="text", text=json.dumps(structured_content, sort_keys=True))],
        structuredContent=structured_content,
        isError=is_error,
    )


def success_result(
    tool_name: str,
    payload,
    status_code: int,
    correlation_id: str,
    envelope_type: type[ToolEnvelope],
) -> CallToolResult:
    envelope = envelope_type(
        ok=True,
        tool_name=tool_name,
        status_code=status_code,
        correlation_id=correlation_id,
        data=payload,
    )
    return tool_result_from_envelope(envelope)


def error_result(
    tool_name: str,
    error: ServiceError,
    correlation_id: str,
    envelope_type: type[ToolEnvelope],
) -> CallToolResult:
    envelope = envelope_type(
        ok=False,
        tool_name=tool_name,
        status_code=ERROR_STATUS_BY_CODE.get(error.code, 500),
        correlation_id=correlation_id,
        error=ToolErrorPayload(
            code=error.code,
            category=error.category,
            retryable=error.retryable,
            message=error.message,
            correlation_id=correlation_id,
        ),
    )
    return tool_result_from_envelope(envelope, is_error=True)


def map_result(
    tool_name: str,
    result: Result,
    correlation_id: str,
    payload_factory: Callable,
    success_status_code: int,
    envelope_type: type[ToolEnvelope],
) -> CallToolResult:
    if result.error is not None:
        return error_result(tool_name, result.error, correlation_id, envelope_type)
    payload = payload_factory(result.value)
    return success_result(tool_name, payload, success_status_code, correlation_id, envelope_type)


def get_vendor_eligibility_tool(
    vendor_id: str,
    correlation_id: str | None = None,
) -> Annotated[CallToolResult, VendorEligibilityToolEnvelope]:
    """Return vendor eligibility information for one vendor."""
    resolved_correlation_id = resolve_correlation_id(correlation_id)
    with session_context() as session:
        result = VendorEligibilityService().get_eligibility(session, vendor_id)
    return map_result(
        "get_vendor_eligibility",
        result,
        resolved_correlation_id,
        lambda value: VendorEligibilityResponse(**value.__dict__),
        200,
        VendorEligibilityToolEnvelope,
    )


def get_vendor_exposure_tool(
    vendor_id: str,
    correlation_id: str | None = None,
) -> Annotated[CallToolResult, VendorExposureToolEnvelope]:
    """Return current vendor exposure and any active credit alert."""
    resolved_correlation_id = resolve_correlation_id(correlation_id)
    with session_context() as session:
        result = VendorExposureService().get_exposure(session, vendor_id)
    return map_result(
        "get_vendor_exposure",
        result,
        resolved_correlation_id,
        VendorExposureResponse.from_domain,
        200,
        VendorExposureToolEnvelope,
    )


def create_purchase_order_tool(
    vendor_id: str,
    line_items: list[PurchaseOrderLineInputRequest],
    idempotency_key: str,
    correlation_id: str | None = None,
) -> Annotated[CallToolResult, PurchaseOrderToolEnvelope]:
    """Create a draft purchase order for an active vendor."""
    resolved_correlation_id = resolve_correlation_id(correlation_id)
    with session_context() as session:
        result = PurchaseOrderService().create_purchase_order(
            session=session,
            vendor_id=vendor_id,
            line_items=[
                PurchaseOrderLineInput(
                    sku=line_item.sku,
                    description=line_item.description,
                    qty_ordered=line_item.qty_ordered,
                    unit_cost=line_item.unit_cost,
                )
                for line_item in line_items
            ],
            idempotency_key=idempotency_key,
        )
    return map_result(
        "create_purchase_order",
        result,
        resolved_correlation_id,
        PurchaseOrderResponse.from_domain,
        201,
        PurchaseOrderToolEnvelope,
    )


def get_purchase_order_tool(
    purchase_order_id: str,
    correlation_id: str | None = None,
) -> Annotated[CallToolResult, PurchaseOrderToolEnvelope]:
    """Return the current state of one purchase order."""
    resolved_correlation_id = resolve_correlation_id(correlation_id)
    with session_context() as session:
        result = PurchaseOrderService().get_purchase_order(session, purchase_order_id)
    return map_result(
        "get_purchase_order",
        result,
        resolved_correlation_id,
        PurchaseOrderResponse.from_domain,
        200,
        PurchaseOrderToolEnvelope,
    )


def submit_purchase_order_tool(
    purchase_order_id: str,
    idempotency_key: str,
    correlation_id: str | None = None,
) -> Annotated[CallToolResult, PurchaseOrderToolEnvelope]:
    """Submit a draft purchase order for downstream receiving and invoicing."""
    resolved_correlation_id = resolve_correlation_id(correlation_id)
    with session_context() as session:
        result = PurchaseOrderService().submit_purchase_order(session, purchase_order_id, idempotency_key)
    return map_result(
        "submit_purchase_order",
        result,
        resolved_correlation_id,
        PurchaseOrderResponse.from_domain,
        200,
        PurchaseOrderToolEnvelope,
    )


def receive_purchase_order_tool(
    purchase_order_id: str,
    received_by: str,
    line_items: list[GoodsReceiptLineInputRequest],
    idempotency_key: str,
    correlation_id: str | None = None,
) -> Annotated[CallToolResult, PurchaseOrderToolEnvelope]:
    """Record a goods receipt against a submitted purchase order."""
    resolved_correlation_id = resolve_correlation_id(correlation_id)
    with session_context() as session:
        result = GoodsReceiptService().receive_goods(
            session=session,
            purchase_order_id=purchase_order_id,
            received_by=received_by,
            line_items=[
                GoodsReceiptLineInput(
                    po_line_item_id=line_item.po_line_item_id,
                    qty_received=line_item.qty_received,
                )
                for line_item in line_items
            ],
            idempotency_key=idempotency_key,
        )
    return map_result(
        "receive_purchase_order",
        result,
        resolved_correlation_id,
        PurchaseOrderResponse.from_domain,
        200,
        PurchaseOrderToolEnvelope,
    )


def create_invoice_tool(
    vendor_id: str,
    purchase_order_id: str,
    invoice_number: str,
    invoice_amount: Decimal,
    idempotency_key: str,
    correlation_id: str | None = None,
) -> Annotated[CallToolResult, InvoiceToolEnvelope]:
    """Register an invoice against a submitted or received purchase order."""
    resolved_correlation_id = resolve_correlation_id(correlation_id)
    with session_context() as session:
        result = InvoiceService().create_invoice(
            session=session,
            vendor_id=vendor_id,
            purchase_order_id=purchase_order_id,
            invoice_number=invoice_number,
            invoice_amount=invoice_amount,
            idempotency_key=idempotency_key,
            correlation_id=resolved_correlation_id,
        )
    return map_result(
        "create_invoice",
        result,
        resolved_correlation_id,
        lambda value: InvoiceResponse.from_domain(value.invoice, credit_check_id=value.credit_check_id),
        201,
        InvoiceToolEnvelope,
    )


def match_invoice_tool(
    invoice_id: str,
    idempotency_key: str,
    correlation_id: str | None = None,
) -> Annotated[CallToolResult, InvoiceMatchToolEnvelope]:
    """Run three-way matching for an invoice."""
    resolved_correlation_id = resolve_correlation_id(correlation_id)
    with session_context() as session:
        result = InvoiceMatchingService().match_invoice(
            session=session,
            invoice_id=invoice_id,
            idempotency_key=idempotency_key,
        )
    if result.error is not None:
        return error_result("match_invoice", result.error, resolved_correlation_id, InvoiceMatchToolEnvelope)
    payload = InvoiceMatchResponse.from_domain(result.value)
    return success_result(
        "match_invoice",
        payload,
        result.value.http_status_code,
        resolved_correlation_id,
        InvoiceMatchToolEnvelope,
    )


def approve_invoice_tool(
    invoice_id: str,
    idempotency_key: str,
    correlation_id: str | None = None,
) -> Annotated[CallToolResult, InvoiceApprovalToolEnvelope]:
    """Approve a matched invoice and surface generated GL entries."""
    resolved_correlation_id = resolve_correlation_id(correlation_id)
    with session_context() as session:
        result = InvoiceApprovalService().approve_invoice(
            session=session,
            invoice_id=invoice_id,
            idempotency_key=idempotency_key,
            correlation_id=resolved_correlation_id,
        )
    return map_result(
        "approve_invoice",
        result,
        resolved_correlation_id,
        InvoiceApprovalResponse.from_domain,
        200,
        InvoiceApprovalToolEnvelope,
    )


def pay_invoice_tool(
    invoice_id: str,
    idempotency_key: str,
    correlation_id: str | None = None,
) -> Annotated[CallToolResult, InvoicePaymentToolEnvelope]:
    """Mark an approved invoice as paid and close the linked purchase order."""
    resolved_correlation_id = resolve_correlation_id(correlation_id)
    with session_context() as session:
        result = InvoicePaymentService().pay_invoice(
            session=session,
            invoice_id=invoice_id,
            idempotency_key=idempotency_key,
        )
    return map_result(
        "pay_invoice",
        result,
        resolved_correlation_id,
        InvoicePaymentResponse.from_domain,
        200,
        InvoicePaymentToolEnvelope,
    )


def get_credit_check_tool(
    credit_check_id: str,
    correlation_id: str | None = None,
) -> Annotated[CallToolResult, CreditCheckToolEnvelope]:
    """Return the state of a background credit-check by identifier."""
    resolved_correlation_id = resolve_correlation_id(correlation_id)
    with session_context() as session:
        result = VendorCreditAlertService().get_credit_check(session, credit_check_id)
    return map_result(
        "get_credit_check",
        result,
        resolved_correlation_id,
        CreditCheckStatusResponse.from_domain,
        200,
        CreditCheckToolEnvelope,
    )


__all__ = [
    "approve_invoice_tool",
    "create_invoice_tool",
    "create_purchase_order_tool",
    "error_result",
    "get_credit_check_tool",
    "get_purchase_order_tool",
    "get_vendor_eligibility_tool",
    "get_vendor_exposure_tool",
    "map_result",
    "match_invoice_tool",
    "pay_invoice_tool",
    "receive_purchase_order_tool",
    "resolve_correlation_id",
    "session_context",
    "submit_purchase_order_tool",
    "success_result",
    "tool_result_from_envelope",
]