from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from src.api.schemas.common import APIModel
from src.domain.models.vendor_credit import CreditAlert


class ActiveCreditAlertResponse(APIModel):
    alert_id: str
    vendor_id: str
    credit_check_id: str
    triggering_invoice_id: str
    outstanding_amount: Decimal
    credit_limit: Decimal
    percentage_consumed: Decimal
    breached_at: datetime
    advisory_only: bool

    @classmethod
    def from_domain(cls, alert: CreditAlert) -> "ActiveCreditAlertResponse":
        return cls(
            alert_id=alert.id,
            vendor_id=alert.vendor_id,
            credit_check_id=alert.credit_check_id,
            triggering_invoice_id=alert.triggering_invoice_id,
            outstanding_amount=alert.outstanding_amount,
            credit_limit=alert.credit_limit,
            percentage_consumed=alert.percentage_consumed,
            breached_at=alert.breached_at,
            advisory_only=alert.advisory_only,
        )


class VendorExposureResponse(APIModel):
    vendor_id: str
    vendor_name: str
    as_of_timestamp: datetime
    outstanding_total_amount: Decimal
    open_invoice_count: int
    included_invoice_statuses: list[str]
    active_credit_alert: ActiveCreditAlertResponse | None = None

    @classmethod
    def from_domain(cls, summary) -> "VendorExposureResponse":
        return cls(
            vendor_id=summary.vendor_id,
            vendor_name=summary.vendor_name,
            as_of_timestamp=summary.as_of_timestamp,
            outstanding_total_amount=summary.outstanding_total_amount,
            open_invoice_count=summary.open_invoice_count,
            included_invoice_statuses=summary.included_invoice_statuses,
            active_credit_alert=(
                ActiveCreditAlertResponse.from_domain(summary.active_credit_alert)
                if summary.active_credit_alert is not None
                else None
            ),
        )
