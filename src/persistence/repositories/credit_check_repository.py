from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from src.domain.models.vendor_credit import CreditCheckRecord
from src.persistence.models.credit_check import CreditCheckRow


class CreditCheckRepository:
    def add(self, session: Session, credit_check: CreditCheckRecord) -> CreditCheckRecord:
        session.add(
            CreditCheckRow(
                id=credit_check.id,
                vendor_id=credit_check.vendor_id,
                triggering_invoice_id=credit_check.triggering_invoice_id,
                triggering_action=credit_check.triggering_action,
                status=credit_check.status,
                breached=credit_check.breached,
                alert_id=credit_check.alert_id,
                correlation_id=credit_check.correlation_id,
                idempotency_key=credit_check.idempotency_key,
                created_at=credit_check.created_at,
                completed_at=credit_check.completed_at,
            )
        )
        session.flush()
        return credit_check

    def get_by_id(self, session: Session, credit_check_id: str) -> CreditCheckRecord | None:
        row = session.get(CreditCheckRow, credit_check_id)
        return self._to_domain(row) if row is not None else None

    def get_by_trigger(self, session: Session, invoice_id: str, triggering_action: str) -> CreditCheckRecord | None:
        stmt = (
            select(CreditCheckRow)
            .where(CreditCheckRow.triggering_invoice_id == invoice_id)
            .where(CreditCheckRow.triggering_action == triggering_action)
            .order_by(desc(CreditCheckRow.created_at))
        )
        row = session.execute(stmt).scalars().first()
        return self._to_domain(row) if row is not None else None

    def get_by_idempotency_key(self, session: Session, idempotency_key: str, triggering_action: str) -> CreditCheckRecord | None:
        stmt = (
            select(CreditCheckRow)
            .where(CreditCheckRow.idempotency_key == idempotency_key)
            .where(CreditCheckRow.triggering_action == triggering_action)
            .order_by(desc(CreditCheckRow.created_at))
        )
        row = session.execute(stmt).scalars().first()
        return self._to_domain(row) if row is not None else None

    def update(self, session: Session, credit_check: CreditCheckRecord) -> CreditCheckRecord:
        row = session.get(CreditCheckRow, credit_check.id)
        if row is None:
            raise ValueError(f"Credit check {credit_check.id} not found for update.")
        row.status = credit_check.status
        row.breached = credit_check.breached
        row.alert_id = credit_check.alert_id
        row.completed_at = credit_check.completed_at
        session.flush()
        return credit_check

    @staticmethod
    def _to_domain(row: CreditCheckRow) -> CreditCheckRecord:
        return CreditCheckRecord(
            id=row.id,
            vendor_id=row.vendor_id,
            triggering_invoice_id=row.triggering_invoice_id,
            triggering_action=row.triggering_action,
            status=row.status,
            breached=row.breached,
            alert_id=row.alert_id,
            correlation_id=row.correlation_id,
            idempotency_key=row.idempotency_key,
            created_at=CreditCheckRepository._normalize_datetime(row.created_at),
            completed_at=CreditCheckRepository._normalize_datetime(row.completed_at),
        )

    @staticmethod
    def _normalize_datetime(value: datetime | None) -> datetime | None:
        if value is None:
            return None
        return value.replace(tzinfo=UTC) if value.tzinfo is None else value