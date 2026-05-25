from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4


INVOICE_STATUS_PENDING = "PENDING"
INVOICE_STATUS_MATCHED = "MATCHED"
INVOICE_STATUS_APPROVED = "APPROVED"
INVOICE_STATUS_PAID = "PAID"

MATCH_OUTCOME_NONE = "NONE"
MATCH_OUTCOME_BLOCKED = "BLOCKED"
MATCH_OUTCOME_WARNING = "MATCHED_WITH_WARNING"
MATCH_OUTCOME_CLEAN = "MATCHED"

REQUEST_MATCH = "REQUEST_MATCH"
WAIT_FOR_RECEIPT = "WAIT_FOR_RECEIPT"
CORRECT_INVOICE = "CORRECT_INVOICE"
PROCEED_TO_APPROVAL = "PROCEED_TO_APPROVAL"
MARK_PAID = "MARK_PAID"
COMPLETE = "COMPLETE"

OPEN_RECEIPT_EXPOSURE = "OPEN_RECEIPT_EXPOSURE"
AP_CONTROL_ACCOUNT = "AP_CONTROL"
UNCLASSIFIED_EXPENSE_ACCOUNT = "UNCLASSIFIED_EXPENSE"


@dataclass(frozen=True)
class OpenLineExposure:
    po_line_item_id: str
    sku: str
    qty_remaining: int
    remaining_value: Decimal


@dataclass(frozen=True)
class OpenExposureWarning:
    code: str
    message: str
    exposure_amount: Decimal
    purchase_order_status: str
    remaining_order_value: Decimal
    open_lines: list[OpenLineExposure]


@dataclass(frozen=True)
class ReceivedValueSnapshot:
    purchase_order_id: str
    received_value: Decimal
    ordered_value: Decimal
    difference_amount: Decimal
    remaining_order_value: Decimal
    is_fully_received: bool
    open_lines: list[OpenLineExposure]
    purchase_order_status: str


@dataclass(frozen=True)
class Invoice:
    id: str
    vendor_id: str
    purchase_order_id: str
    invoice_number: str
    invoice_amount: Decimal
    status: str
    last_match_outcome: str
    created_at: datetime
    matched_at: datetime | None = None
    approved_at: datetime | None = None
    paid_at: datetime | None = None


@dataclass(frozen=True)
class GLEntry:
    id: str
    invoice_id: str
    account_code: str
    debit: Decimal
    credit: Decimal
    posted_at: datetime


@dataclass(frozen=True)
class InvoiceMatchResult:
    snapshot_id: str
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
    open_lines: list[OpenLineExposure]
    next_action: str
    evaluated_at: datetime
    purchase_order_status: str
    matched_at: datetime | None = None
    shortfall_amount: Decimal | None = None
    warning: OpenExposureWarning | None = None
    idempotency_key: str | None = None

    @property
    def http_status_code(self) -> int:
        if self.match_status == MATCH_OUTCOME_BLOCKED:
            return 422
        if self.match_status == MATCH_OUTCOME_WARNING:
            return 202
        return 200


@dataclass(frozen=True)
class InvoiceApprovalResult:
    invoice_id: str
    purchase_order_id: str
    invoice_status: str
    generated_gl_entries: list[GLEntry]
    approved_at: datetime
    next_action: str


@dataclass(frozen=True)
class InvoicePaymentResult:
    invoice_id: str
    purchase_order_id: str
    invoice_status: str
    purchase_order_status: str
    paid_at: datetime
    next_action: str


def build_pending_invoice(
    vendor_id: str,
    purchase_order_id: str,
    invoice_number: str,
    invoice_amount: Decimal,
    created_at: datetime | None = None,
) -> Invoice:
    timestamp = created_at or datetime.now(UTC)
    invoice_id = f"INV-{uuid4().hex[:8].upper()}"
    return Invoice(
        id=invoice_id,
        vendor_id=vendor_id,
        purchase_order_id=purchase_order_id,
        invoice_number=invoice_number,
        invoice_amount=invoice_amount.quantize(Decimal("0.01")),
        status=INVOICE_STATUS_PENDING,
        last_match_outcome=MATCH_OUTCOME_NONE,
        created_at=timestamp,
    )


def apply_match_result(invoice: Invoice, match_result: InvoiceMatchResult) -> Invoice:
    if match_result.match_status == MATCH_OUTCOME_BLOCKED:
        return replace(invoice, last_match_outcome=MATCH_OUTCOME_BLOCKED)
    return replace(
        invoice,
        status=INVOICE_STATUS_MATCHED,
        last_match_outcome=match_result.match_status,
        matched_at=match_result.matched_at,
    )


def apply_invoice_approval(invoice: Invoice, approved_at: datetime | None = None) -> Invoice:
    return replace(
        invoice,
        status=INVOICE_STATUS_APPROVED,
        approved_at=approved_at or datetime.now(UTC),
    )


def apply_invoice_payment(invoice: Invoice, paid_at: datetime | None = None) -> Invoice:
    return replace(
        invoice,
        status=INVOICE_STATUS_PAID,
        paid_at=paid_at or datetime.now(UTC),
    )


def build_open_exposure_warning(
    purchase_order_status: str,
    remaining_order_value: Decimal,
    open_lines: list[OpenLineExposure],
) -> OpenExposureWarning:
    normalized_remaining_order_value = remaining_order_value.quantize(Decimal("0.01"))
    return OpenExposureWarning(
        code=OPEN_RECEIPT_EXPOSURE,
        message="Purchase order still has open receipt exposure.",
        exposure_amount=normalized_remaining_order_value,
        purchase_order_status=purchase_order_status,
        remaining_order_value=normalized_remaining_order_value,
        open_lines=open_lines,
    )