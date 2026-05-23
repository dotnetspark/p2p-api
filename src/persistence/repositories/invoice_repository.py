from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.persistence.models.invoice import InvoiceRow


UNPAID_STATUSES = ["PENDING", "MATCHED", "APPROVED"]


@dataclass(frozen=True)
class ExposureAggregate:
    as_of_timestamp: datetime
    outstanding_total_amount: Decimal
    open_invoice_count: int
    included_invoice_statuses: list[str]


class InvoiceRepository:
    def get_exposure_aggregate(self, session: Session, vendor_id: str) -> ExposureAggregate:
        stmt = (
            select(
                func.coalesce(func.sum(InvoiceRow.amount), 0),
                func.count(InvoiceRow.id),
            )
            .where(InvoiceRow.vendor_id == vendor_id)
            .where(InvoiceRow.status.in_(UNPAID_STATUSES))
        )
        total, count = session.execute(stmt).one()
        normalized_total = Decimal(total).quantize(Decimal("0.01")) if not isinstance(total, Decimal) else total.quantize(Decimal("0.01"))
        return ExposureAggregate(
            as_of_timestamp=datetime.now(UTC),
            outstanding_total_amount=normalized_total,
            open_invoice_count=count,
            included_invoice_statuses=list(UNPAID_STATUSES),
        )

