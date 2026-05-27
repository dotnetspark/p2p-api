from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.domain.models.invoice import AP_CONTROL_ACCOUNT, GLEntry
from src.persistence.models.gl_entry import GLEntryRow


class GLEntryRepository:
    def add_many(self, session: Session, gl_entries: list[GLEntry]) -> list[GLEntry]:
        session.add_all(
            [
                GLEntryRow(
                    id=gl_entry.id,
                    invoice_id=gl_entry.invoice_id,
                    account_code=gl_entry.account_code,
                    debit=gl_entry.debit,
                    credit=gl_entry.credit,
                    posted_at=gl_entry.posted_at,
                )
                for gl_entry in gl_entries
            ]
        )
        session.flush()
        return gl_entries

    def list_by_invoice_id(self, session: Session, invoice_id: str) -> list[GLEntry]:
        stmt = (
            select(GLEntryRow)
            .where(GLEntryRow.invoice_id == invoice_id)
            .order_by(GLEntryRow.posted_at, GLEntryRow.id)
        )
        rows = session.execute(stmt).scalars().all()
        gl_entries = [self._to_domain(row) for row in rows]
        return sorted(
            gl_entries,
            key=lambda entry: (
                entry.account_code == AP_CONTROL_ACCOUNT,
                entry.account_code,
                entry.id,
            ),
        )

    @staticmethod
    def _to_domain(row: GLEntryRow) -> GLEntry:
        return GLEntry(
            id=row.id,
            invoice_id=row.invoice_id,
            account_code=row.account_code,
            debit=Decimal(row.debit).quantize(Decimal("0.01")),
            credit=Decimal(row.credit).quantize(Decimal("0.01")),
            posted_at=GLEntryRepository._normalize_datetime(row.posted_at),
        )

    @staticmethod
    def _normalize_datetime(value: datetime) -> datetime:
        return value.replace(tzinfo=UTC) if value.tzinfo is None else value