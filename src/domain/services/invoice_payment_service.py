from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from src.core.errors import (
    ServiceError,
    dependency_temporarily_unavailable,
    idempotency_key_conflict,
    invoice_invalid_state,
    invoice_not_found,
    purchase_order_not_found,
)
from src.core.idempotency import build_idempotency_fingerprint
from src.core.results import Result
from src.domain.models.invoice import COMPLETE, INVOICE_STATUS_APPROVED, INVOICE_STATUS_PAID, InvoicePaymentResult, apply_invoice_payment
from src.domain.models.purchase_order import close_purchase_order_for_payment
from src.persistence.repositories.idempotency_repository import IdempotencyRepository
from src.persistence.repositories.invoice_repository import InvoiceRepository
from src.persistence.repositories.purchase_order_repository import PurchaseOrderRepository


PAY_INVOICE_OPERATION = "invoice.pay"


class InvoicePaymentService:
    def __init__(
        self,
        invoice_repository: InvoiceRepository | None = None,
        purchase_order_repository: PurchaseOrderRepository | None = None,
        idempotency_repository: IdempotencyRepository | None = None,
    ) -> None:
        self.invoice_repository = invoice_repository or InvoiceRepository()
        self.purchase_order_repository = purchase_order_repository or PurchaseOrderRepository()
        self.idempotency_repository = idempotency_repository or IdempotencyRepository()

    def pay_invoice(
        self,
        session: Session,
        invoice_id: str,
        idempotency_key: str,
    ) -> Result[InvoicePaymentResult, ServiceError]:
        request_fingerprint = build_idempotency_fingerprint(
            PAY_INVOICE_OPERATION,
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
        if invoice.status != INVOICE_STATUS_APPROVED:
            return Result.fail(invoice_invalid_state(invoice_id, invoice.status, "invoice payment"))

        purchase_order = self.purchase_order_repository.get_by_id(session, invoice.purchase_order_id)
        if purchase_order is None:
            return Result.fail(purchase_order_not_found(invoice.purchase_order_id))

        purchase_order_result = close_purchase_order_for_payment(purchase_order)
        if purchase_order_result.error is not None:
            return Result.fail(purchase_order_result.error)

        paid_at = datetime.now(UTC)
        updated_invoice = apply_invoice_payment(invoice, paid_at=paid_at)
        updated_purchase_order = purchase_order_result.value

        try:
            self.invoice_repository.update(session, updated_invoice)
            self.purchase_order_repository.update(session, updated_purchase_order)
            self.idempotency_repository.add(
                session,
                key=idempotency_key,
                operation=PAY_INVOICE_OPERATION,
                request_fingerprint=request_fingerprint,
                resource_id=invoice.id,
            )
            session.commit()
        except Exception:
            session.rollback()
            return Result.fail(dependency_temporarily_unavailable())

        return Result.ok(
            InvoicePaymentResult(
                invoice_id=updated_invoice.id,
                purchase_order_id=updated_invoice.purchase_order_id,
                invoice_status=updated_invoice.status,
                purchase_order_status=updated_purchase_order.status,
                paid_at=paid_at,
                next_action=COMPLETE,
            )
        )

    def _resolve_idempotency(
        self,
        session: Session,
        idempotency_key: str,
        request_fingerprint: str,
    ) -> Result[InvoicePaymentResult, ServiceError] | None:
        existing_record = self.idempotency_repository.get_by_key(session, idempotency_key)
        if existing_record is None:
            return None
        if (
            existing_record.operation != PAY_INVOICE_OPERATION
            or existing_record.request_fingerprint != request_fingerprint
        ):
            return Result.fail(idempotency_key_conflict(idempotency_key))

        invoice = self.invoice_repository.get_by_id(session, existing_record.resource_id)
        if invoice is None or invoice.status != INVOICE_STATUS_PAID or invoice.paid_at is None:
            return Result.fail(dependency_temporarily_unavailable())

        purchase_order = self.purchase_order_repository.get_by_id(session, invoice.purchase_order_id)
        if purchase_order is None:
            return Result.fail(purchase_order_not_found(invoice.purchase_order_id))

        return Result.ok(
            InvoicePaymentResult(
                invoice_id=invoice.id,
                purchase_order_id=invoice.purchase_order_id,
                invoice_status=invoice.status,
                purchase_order_status=purchase_order.status,
                paid_at=invoice.paid_at,
                next_action=COMPLETE,
            )
        )