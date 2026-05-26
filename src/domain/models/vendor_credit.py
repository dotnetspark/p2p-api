from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
from uuid import uuid4


CREDIT_CHECK_ACTION_CREATE = "CREATE"
CREDIT_CHECK_ACTION_APPROVE = "APPROVE"

CREDIT_CHECK_STATUS_PENDING = "PENDING"
CREDIT_CHECK_STATUS_COMPLETED = "COMPLETED"

CREDIT_ALERT_STATUS_ACTIVE = "ACTIVE"


@dataclass(frozen=True)
class CreditCheckRecord:
    id: str
    vendor_id: str
    triggering_invoice_id: str
    triggering_action: str
    status: str
    breached: bool | None
    alert_id: str | None
    correlation_id: str
    idempotency_key: str
    created_at: datetime
    completed_at: datetime | None = None


@dataclass(frozen=True)
class CreditAlert:
    id: str
    vendor_id: str
    credit_check_id: str
    triggering_invoice_id: str
    outstanding_amount: Decimal
    credit_limit: Decimal
    percentage_consumed: Decimal
    breached_at: datetime
    status: str
    advisory_only: bool = True


@dataclass(frozen=True)
class CreditCheckQueryResult:
    status: str
    breached: bool | None
    alert_id: str | None


def create_pending_credit_check(
    vendor_id: str,
    triggering_invoice_id: str,
    triggering_action: str,
    correlation_id: str,
    idempotency_key: str,
    created_at: datetime | None = None,
) -> CreditCheckRecord:
    timestamp = created_at or datetime.now(UTC)
    return CreditCheckRecord(
        id=f"CHK-{uuid4().hex[:8].upper()}",
        vendor_id=vendor_id,
        triggering_invoice_id=triggering_invoice_id,
        triggering_action=triggering_action,
        status=CREDIT_CHECK_STATUS_PENDING,
        breached=None,
        alert_id=None,
        correlation_id=correlation_id,
        idempotency_key=idempotency_key,
        created_at=timestamp,
        completed_at=None,
    )


def complete_credit_check(
    credit_check: CreditCheckRecord,
    breached: bool,
    alert_id: str | None,
    completed_at: datetime | None = None,
) -> CreditCheckRecord:
    return replace(
        credit_check,
        status=CREDIT_CHECK_STATUS_COMPLETED,
        breached=breached,
        alert_id=alert_id,
        completed_at=completed_at or datetime.now(UTC),
    )


def create_credit_alert(
    vendor_id: str,
    credit_check_id: str,
    triggering_invoice_id: str,
    outstanding_amount: Decimal,
    credit_limit: Decimal,
    breached_at: datetime | None = None,
) -> CreditAlert:
    normalized_outstanding = outstanding_amount.quantize(Decimal("0.01"))
    normalized_credit_limit = credit_limit.quantize(Decimal("0.01"))
    percentage_consumed = Decimal("0.00")
    if normalized_credit_limit != Decimal("0.00"):
        percentage_consumed = (
            (normalized_outstanding / normalized_credit_limit) * Decimal("100")
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return CreditAlert(
        id=f"ALERT-{uuid4().hex[:8].upper()}",
        vendor_id=vendor_id,
        credit_check_id=credit_check_id,
        triggering_invoice_id=triggering_invoice_id,
        outstanding_amount=normalized_outstanding,
        credit_limit=normalized_credit_limit,
        percentage_consumed=percentage_consumed,
        breached_at=breached_at or datetime.now(UTC),
        status=CREDIT_ALERT_STATUS_ACTIVE,
        advisory_only=True,
    )