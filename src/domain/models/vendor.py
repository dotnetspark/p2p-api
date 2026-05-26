from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, UTC
from decimal import Decimal

from src.domain.models.vendor_credit import CreditAlert


@dataclass(frozen=True)
class Vendor:
    id: str
    name: str
    payment_terms: str
    credit_limit: Decimal
    is_active: bool


@dataclass(frozen=True)
class VendorEligibilityResult:
    vendor_id: str
    vendor_name: str
    is_active: bool
    obligations_allowed: bool
    blocking_reason_code: str | None = None
    blocking_reason_message: str | None = None


@dataclass(frozen=True)
class OutstandingPaymentObligationSummary:
    vendor_id: str
    vendor_name: str
    as_of_timestamp: datetime
    outstanding_total_amount: Decimal
    open_invoice_count: int
    included_invoice_statuses: list[str]
    active_credit_alert: CreditAlert | None = None

    @classmethod
    def zero(cls, vendor_id: str, vendor_name: str, included_invoice_statuses: list[str]) -> "OutstandingPaymentObligationSummary":
        return cls(
            vendor_id=vendor_id,
            vendor_name=vendor_name,
            as_of_timestamp=datetime.now(UTC),
            outstanding_total_amount=Decimal("0.00"),
            open_invoice_count=0,
            included_invoice_statuses=included_invoice_statuses,
        )
