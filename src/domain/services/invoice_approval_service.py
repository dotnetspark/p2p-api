from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from src.core.errors import (
    ServiceError,
    dependency_temporarily_unavailable,
    gl_entries_missing,
    gl_entries_unbalanced,
    idempotency_key_conflict,
    invoice_invalid_state,
    invoice_not_found,
)
from src.core.idempotency import build_idempotency_fingerprint
from src.core.results import Result
from src.domain.models.invoice import (
    INVOICE_STATUS_APPROVED,
    INVOICE_STATUS_MATCHED,
    InvoiceApprovalResult,
    MARK_PAID,
    apply_invoice_approval,
)
from src.domain.rules.gl_posting import build_balanced_gl_entries, gl_entries_are_balanced, resolve_expense_account_code
from src.persistence.repositories.gl_entry_repository import GLEntryRepository
from src.persistence.repositories.idempotency_repository import IdempotencyRepository
from src.persistence.repositories.invoice_repository import InvoiceRepository
from src.persistence.repositories.vendor_repository import VendorRepository


APPROVE_INVOICE_OPERATION = "invoice.approve"


class InvoiceApprovalService:
    def __init__(
        self,
        invoice_repository: InvoiceRepository | None = None,
        vendor_repository: VendorRepository | None = None,
        gl_entry_repository: GLEntryRepository | None = None,
        idempotency_repository: IdempotencyRepository | None = None,
    ) -> None:
        self.invoice_repository = invoice_repository or InvoiceRepository()
        self.vendor_repository = vendor_repository or VendorRepository()
        self.gl_entry_repository = gl_entry_repository or GLEntryRepository()
        self.idempotency_repository = idempotency_repository or IdempotencyRepository()

    def approve_invoice(
        self,
        session: Session,
        invoice_id: str,
        idempotency_key: str,
    ) -> Result[InvoiceApprovalResult, ServiceError]:
        request_fingerprint = build_idempotency_fingerprint(
            APPROVE_INVOICE_OPERATION,
            {"invoice_id": invoice_id},
        )
        idempotency_result = self._resolve_idempotency(
            session=session,
            idempotency_key=idempotency_key,
            request_fingerprint=request_fingerprint,
        )
        if idempotency_result is not None:
            return idempotency_result

        invoice = self.invoice_repository.get_by_id(session, invoice_id)
        if invoice is None:
            return Result.fail(invoice_not_found(invoice_id))
        if invoice.status != INVOICE_STATUS_MATCHED:
            return Result.fail(invoice_invalid_state(invoice_id, invoice.status, "invoice approval"))

        vendor = self.vendor_repository.get_by_id(session, invoice.vendor_id)
        if vendor is None:
            return Result.fail(dependency_temporarily_unavailable())

        approved_at = datetime.now(UTC)
        updated_invoice = apply_invoice_approval(invoice, approved_at=approved_at)
        expense_account_code = resolve_expense_account_code(vendor)
        gl_entries = build_balanced_gl_entries(
            invoice_id=invoice.id,
            invoice_amount=invoice.invoice_amount,
            expense_account_code=expense_account_code,
            posted_at=approved_at,
        )
        if not gl_entries_are_balanced(gl_entries):
            return Result.fail(gl_entries_unbalanced(invoice.id))

        try:
            self.invoice_repository.update(session, updated_invoice)
            self.gl_entry_repository.add_many(session, gl_entries)
            self.idempotency_repository.add(
                session,
                key=idempotency_key,
                operation=APPROVE_INVOICE_OPERATION,
                request_fingerprint=request_fingerprint,
                resource_id=invoice.id,
            )
            session.commit()
        except Exception:
            session.rollback()
            return Result.fail(dependency_temporarily_unavailable())

        return Result.ok(
            InvoiceApprovalResult(
                invoice_id=updated_invoice.id,
                purchase_order_id=updated_invoice.purchase_order_id,
                invoice_status=updated_invoice.status,
                generated_gl_entries=gl_entries,
                approved_at=approved_at,
                next_action=MARK_PAID,
            )
        )

    def _resolve_idempotency(
        self,
        session: Session,
        idempotency_key: str,
        request_fingerprint: str,
    ) -> Result[InvoiceApprovalResult, ServiceError] | None:
        existing_record = self.idempotency_repository.get_by_key(session, idempotency_key)
        if existing_record is None:
            return None
        if (
            existing_record.operation != APPROVE_INVOICE_OPERATION
            or existing_record.request_fingerprint != request_fingerprint
        ):
            return Result.fail(idempotency_key_conflict(idempotency_key))

        invoice = self.invoice_repository.get_by_id(session, existing_record.resource_id)
        if invoice is None or invoice.status != INVOICE_STATUS_APPROVED or invoice.approved_at is None:
            return Result.fail(dependency_temporarily_unavailable())

        gl_entries = self.gl_entry_repository.list_by_invoice_id(session, invoice.id)
        if not gl_entries:
            return Result.fail(gl_entries_missing(invoice.id))
        if not gl_entries_are_balanced(gl_entries):
            return Result.fail(gl_entries_unbalanced(invoice.id))

        return Result.ok(
            InvoiceApprovalResult(
                invoice_id=invoice.id,
                purchase_order_id=invoice.purchase_order_id,
                invoice_status=invoice.status,
                generated_gl_entries=gl_entries,
                approved_at=invoice.approved_at,
                next_action=MARK_PAID,
            )
        )