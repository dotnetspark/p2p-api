from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import Field

from src.api.schemas.common import APIModel
from src.domain.models.invoice import Invoice, InvoiceMatchResult, OpenExposureWarning, OpenLineExposure


class CreateInvoiceRequest(APIModel):
    vendor_id: str
    purchase_order_id: str
    invoice_number: str
    invoice_amount: Decimal = Field(..., gt=0, decimal_places=2)


class InvoiceResponse(APIModel):
    invoice_id: str
    vendor_id: str
    purchase_order_id: str
    invoice_number: str
    invoice_amount: Decimal
    status: str
    last_match_outcome: str
    next_action: str

    @classmethod
    def from_domain(cls, invoice: Invoice) -> "InvoiceResponse":
        return cls(
            invoice_id=invoice.id,
            vendor_id=invoice.vendor_id,
            purchase_order_id=invoice.purchase_order_id,
            invoice_number=invoice.invoice_number,
            invoice_amount=invoice.invoice_amount,
            status=invoice.status,
            last_match_outcome=invoice.last_match_outcome,
            next_action="REQUEST_MATCH",
        )


class OpenLineExposureResponse(APIModel):
    po_line_item_id: str
    sku: str
    qty_remaining: int
    remaining_value: Decimal

    @classmethod
    def from_domain(cls, open_line: OpenLineExposure) -> "OpenLineExposureResponse":
        return cls(
            po_line_item_id=open_line.po_line_item_id,
            sku=open_line.sku,
            qty_remaining=open_line.qty_remaining,
            remaining_value=open_line.remaining_value,
        )


class OpenExposureWarningResponse(APIModel):
    code: str
    message: str
    exposure_amount: Decimal
    purchase_order_status: str
    remaining_order_value: Decimal
    open_lines: list[OpenLineExposureResponse]

    @classmethod
    def from_domain(cls, warning: OpenExposureWarning) -> "OpenExposureWarningResponse":
        return cls(
            code=warning.code,
            message=warning.message,
            exposure_amount=warning.exposure_amount,
            purchase_order_status=warning.purchase_order_status,
            remaining_order_value=warning.remaining_order_value,
            open_lines=[OpenLineExposureResponse.from_domain(line) for line in warning.open_lines],
        )


class InvoiceMatchResponse(APIModel):
    invoice_id: str
    purchase_order_id: str
    invoice_status: str
    last_match_outcome: str
    match_status: str
    invoice_amount: Decimal
    received_value: Decimal
    ordered_value: Decimal
    difference_amount: Decimal
    remaining_order_value: Decimal
    all_lines_fully_received: bool
    open_lines: list[OpenLineExposureResponse]
    next_action: str
    matched_at: datetime | None = None
    shortfall_amount: Decimal | None = None
    warning: OpenExposureWarningResponse | None = None

    @classmethod
    def from_domain(cls, result: InvoiceMatchResult) -> "InvoiceMatchResponse":
        return cls(
            invoice_id=result.invoice_id,
            purchase_order_id=result.purchase_order_id,
            invoice_status=result.invoice_status,
            last_match_outcome=result.last_match_outcome,
            match_status=result.match_status,
            invoice_amount=result.invoice_amount,
            received_value=result.received_value,
            ordered_value=result.ordered_value,
            difference_amount=result.difference_amount,
            remaining_order_value=result.remaining_order_value,
            all_lines_fully_received=result.all_lines_fully_received,
            open_lines=[OpenLineExposureResponse.from_domain(line) for line in result.open_lines],
            next_action=result.next_action,
            matched_at=result.matched_at,
            shortfall_amount=result.shortfall_amount,
            warning=(OpenExposureWarningResponse.from_domain(result.warning) if result.warning is not None else None),
        )