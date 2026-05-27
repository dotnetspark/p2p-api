from __future__ import annotations

from decimal import Decimal
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

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


PayloadT = TypeVar("PayloadT", bound=BaseModel)


class MCPModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True, str_strip_whitespace=True)


class ToolErrorPayload(MCPModel):
    code: str
    category: str
    retryable: bool
    message: str
    correlation_id: str


class ToolEnvelope(MCPModel, Generic[PayloadT]):
    ok: bool
    tool_name: str
    status_code: int
    correlation_id: str
    data: PayloadT | None = None
    error: ToolErrorPayload | None = None


class CreateInvoiceToolPayload(MCPModel):
    vendor_id: str
    purchase_order_id: str
    invoice_number: str
    invoice_amount: Decimal = Field(..., gt=0, decimal_places=2)


VendorEligibilityToolEnvelope = ToolEnvelope[VendorEligibilityResponse]
VendorExposureToolEnvelope = ToolEnvelope[VendorExposureResponse]
PurchaseOrderToolEnvelope = ToolEnvelope[PurchaseOrderResponse]
InvoiceToolEnvelope = ToolEnvelope[InvoiceResponse]
InvoiceMatchToolEnvelope = ToolEnvelope[InvoiceMatchResponse]
InvoiceApprovalToolEnvelope = ToolEnvelope[InvoiceApprovalResponse]
InvoicePaymentToolEnvelope = ToolEnvelope[InvoicePaymentResponse]
CreditCheckToolEnvelope = ToolEnvelope[CreditCheckStatusResponse]


__all__ = [
    "CreateInvoiceToolPayload",
    "CreditCheckStatusResponse",
    "CreditCheckToolEnvelope",
    "GoodsReceiptLineInputRequest",
    "InvoiceApprovalResponse",
    "InvoiceApprovalToolEnvelope",
    "InvoiceMatchResponse",
    "InvoiceMatchToolEnvelope",
    "InvoicePaymentResponse",
    "InvoicePaymentToolEnvelope",
    "InvoiceResponse",
    "InvoiceToolEnvelope",
    "MCPModel",
    "PayloadT",
    "PurchaseOrderLineInputRequest",
    "PurchaseOrderResponse",
    "PurchaseOrderToolEnvelope",
    "ToolEnvelope",
    "ToolErrorPayload",
    "VendorEligibilityResponse",
    "VendorEligibilityToolEnvelope",
    "VendorExposureResponse",
    "VendorExposureToolEnvelope",
]