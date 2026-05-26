from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from src.persistence.models.idempotency import IdempotencyKeyRow


@dataclass(frozen=True)
class IdempotencyRecord:
    key: str
    operation: str
    request_fingerprint: str
    resource_id: str
    credit_check_id: str | None
    created_at: datetime


class IdempotencyRepository:
    def get_by_key(self, session: Session, key: str) -> IdempotencyRecord | None:
        row = session.get(IdempotencyKeyRow, key)
        if row is None:
            return None
        return IdempotencyRecord(
            key=row.key,
            operation=row.operation,
            request_fingerprint=row.request_fingerprint,
            resource_id=row.resource_id,
            credit_check_id=row.credit_check_id,
            created_at=row.created_at,
        )

    def add(
        self,
        session: Session,
        key: str,
        operation: str,
        request_fingerprint: str,
        resource_id: str,
        credit_check_id: str | None = None,
    ) -> IdempotencyRecord:
        record = IdempotencyRecord(
            key=key,
            operation=operation,
            request_fingerprint=request_fingerprint,
            resource_id=resource_id,
            credit_check_id=credit_check_id,
            created_at=datetime.now(UTC),
        )
        session.add(
            IdempotencyKeyRow(
                key=record.key,
                operation=record.operation,
                request_fingerprint=record.request_fingerprint,
                resource_id=record.resource_id,
                credit_check_id=record.credit_check_id,
                created_at=record.created_at,
            )
        )
        session.flush()
        return record