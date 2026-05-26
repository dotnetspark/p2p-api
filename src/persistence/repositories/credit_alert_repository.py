from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.domain.models.vendor_credit import CreditAlert
from src.persistence.models.credit_alert import CreditAlertRow


class CreditAlertRepository:
    def get_active_by_vendor_id(self, session: Session, vendor_id: str) -> CreditAlert | None:
        stmt = select(CreditAlertRow).where(CreditAlertRow.vendor_id == vendor_id)
        row = session.execute(stmt).scalar_one_or_none()
        return self._to_domain(row) if row is not None else None

    def upsert_active(self, session: Session, alert: CreditAlert) -> CreditAlert:
        row = session.execute(
            select(CreditAlertRow).where(CreditAlertRow.vendor_id == alert.vendor_id)
        ).scalar_one_or_none()
        if row is None:
            session.add(
                CreditAlertRow(
                    id=alert.id,
                    vendor_id=alert.vendor_id,
                    credit_check_id=alert.credit_check_id,
                    triggering_invoice_id=alert.triggering_invoice_id,
                    outstanding_amount=alert.outstanding_amount,
                    credit_limit=alert.credit_limit,
                    percentage_consumed=alert.percentage_consumed,
                    breached_at=alert.breached_at,
                    status=alert.status,
                    advisory_only=alert.advisory_only,
                )
            )
            session.flush()
            return alert
        row.id = alert.id
        row.credit_check_id = alert.credit_check_id
        row.triggering_invoice_id = alert.triggering_invoice_id
        row.outstanding_amount = alert.outstanding_amount
        row.credit_limit = alert.credit_limit
        row.percentage_consumed = alert.percentage_consumed
        row.breached_at = alert.breached_at
        row.status = alert.status
        row.advisory_only = alert.advisory_only
        session.flush()
        return alert

    def clear_active(self, session: Session, vendor_id: str) -> None:
        row = session.execute(
            select(CreditAlertRow).where(CreditAlertRow.vendor_id == vendor_id)
        ).scalar_one_or_none()
        if row is not None:
            session.delete(row)
            session.flush()

    @staticmethod
    def _to_domain(row: CreditAlertRow) -> CreditAlert:
        return CreditAlert(
            id=row.id,
            vendor_id=row.vendor_id,
            credit_check_id=row.credit_check_id,
            triggering_invoice_id=row.triggering_invoice_id,
            outstanding_amount=Decimal(row.outstanding_amount).quantize(Decimal("0.01")),
            credit_limit=Decimal(row.credit_limit).quantize(Decimal("0.01")),
            percentage_consumed=Decimal(row.percentage_consumed).quantize(Decimal("0.01")),
            breached_at=CreditAlertRepository._normalize_datetime(row.breached_at),
            status=row.status,
            advisory_only=row.advisory_only,
        )

    @staticmethod
    def _normalize_datetime(value: datetime) -> datetime:
        return value.replace(tzinfo=UTC) if value.tzinfo is None else value