from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

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
from src.domain.models.invoice import (
    BLOCKED,
    CORRECT_INVOICE,
    InvoiceMatchResult,
    MATCHED,
    MATCHED_CLEAN,
    MATCHED_WITH_WARNING,
    PENDING,
    PROCEED_TO_APPROVAL,
    WAIT_FOR_RECEIPT,
    apply_match_result,
    build_open_exposure_warning,
)
from src.persistence.repositories.idempotency_repository import IdempotencyRepository
from src.persistence.repositories.invoice_repository import InvoiceRepository
from src.persistence.repositories.purchase_order_repository import PurchaseOrderRepository


MATCH_INVOICE_OPERATION = "invoice.match"


class InvoiceMatchingService:
    def __init__(
        self,
        invoice_repository: InvoiceRepository | None = None,
        purchase_order_repository: PurchaseOrderRepository | None = None,
        idempotency_repository: IdempotencyRepository | None = None,
    ) -> None:
        self.invoice_repository = invoice_repository or InvoiceRepository()
        self.purchase_order_repository = purchase_order_repository or PurchaseOrderRepository()
        self.idempotency_repository = idempotency_repository or IdempotencyRepository()

    def match_invoice(
        self,
        session: Session,
        invoice_id: str,
        idempotency_key: str,
    ) -> Result[InvoiceMatchResult, ServiceError]:
        request_fingerprint = build_idempotency_fingerprint(
            MATCH_INVOICE_OPERATION,
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
        if invoice.status not in {PENDING, MATCHED}:
            return Result.fail(invoice_invalid_state(invoice_id, invoice.status, "invoice matching"))

        purchase_order = self.purchase_order_repository.get_by_id(session, invoice.purchase_order_id)
        if purchase_order is None:
            return Result.fail(purchase_order_not_found(invoice.purchase_order_id))
        receipt_snapshot = self.purchase_order_repository.get_received_value_snapshot(
            session,
            invoice.purchase_order_id,
            invoice.invoice_amount,
        )
        if receipt_snapshot is None:
            return Result.fail(purchase_order_not_found(invoice.purchase_order_id))

        evaluated_at = datetime.now(UTC)
        match_result = self._build_match_result(
            invoice_id=invoice.id,
            purchase_order_id=invoice.purchase_order_id,
            invoice_amount=invoice.invoice_amount,
            receipt_snapshot=receipt_snapshot,
            evaluated_at=evaluated_at,
            idempotency_key=idempotency_key,
        )
        updated_invoice = apply_match_result(invoice, match_result)

        try:
            self.invoice_repository.update(session, updated_invoice)
            self.invoice_repository.add_match_snapshot(session, match_result)
            self.idempotency_repository.add(
                session,
                key=idempotency_key,
                operation=MATCH_INVOICE_OPERATION,
                request_fingerprint=request_fingerprint,
                resource_id=match_result.snapshot_id,
            )
            session.commit()
        except Exception:
            session.rollback()
            return Result.fail(dependency_temporarily_unavailable())
        return Result.ok(match_result)

    def _resolve_idempotency(
        self,
        session: Session,
        idempotency_key: str,
        request_fingerprint: str,
    ) -> Result[InvoiceMatchResult, ServiceError] | None:
        existing_record = self.idempotency_repository.get_by_key(session, idempotency_key)
        if existing_record is None:
            return None
        if (
            existing_record.operation != MATCH_INVOICE_OPERATION
            or existing_record.request_fingerprint != request_fingerprint
        ):
            return Result.fail(idempotency_key_conflict(idempotency_key))
        existing_snapshot = self.invoice_repository.get_match_snapshot_by_id(session, existing_record.resource_id)
        if existing_snapshot is None:
            return Result.fail(dependency_temporarily_unavailable())
        return Result.ok(existing_snapshot)

    @staticmethod
    def _build_match_result(
        invoice_id: str,
        purchase_order_id: str,
        invoice_amount: Decimal,
        receipt_snapshot,
        evaluated_at: datetime,
        idempotency_key: str,
    ) -> InvoiceMatchResult:
        snapshot_id = f"IMS-{uuid4().hex[:8].upper()}"
        difference_amount = receipt_snapshot.difference_amount.quantize(Decimal("0.01"))
        remaining_order_value = receipt_snapshot.remaining_order_value.quantize(Decimal("0.01"))
        if receipt_snapshot.received_value < invoice_amount:
            shortfall_amount = (invoice_amount - receipt_snapshot.received_value).quantize(Decimal("0.01"))
            next_action = WAIT_FOR_RECEIPT if invoice_amount <= receipt_snapshot.ordered_value else CORRECT_INVOICE
            return InvoiceMatchResult(
                snapshot_id=snapshot_id,
                invoice_id=invoice_id,
                purchase_order_id=purchase_order_id,
                invoice_status=PENDING,
                last_match_outcome=BLOCKED,
                match_status=BLOCKED,
                invoice_amount=invoice_amount,
                received_value=receipt_snapshot.received_value,
                ordered_value=receipt_snapshot.ordered_value,
                difference_amount=difference_amount,
                remaining_order_value=remaining_order_value,
                all_lines_fully_received=receipt_snapshot.is_fully_received,
                open_lines=receipt_snapshot.open_lines,
                next_action=next_action,
                evaluated_at=evaluated_at,
                purchase_order_status=receipt_snapshot.purchase_order_status,
                shortfall_amount=shortfall_amount,
                idempotency_key=idempotency_key,
            )

        matched_at = evaluated_at
        if not receipt_snapshot.is_fully_received:
            warning = build_open_exposure_warning(
                purchase_order_status=receipt_snapshot.purchase_order_status,
                remaining_order_value=remaining_order_value,
                open_lines=receipt_snapshot.open_lines,
            )
            return InvoiceMatchResult(
                snapshot_id=snapshot_id,
                invoice_id=invoice_id,
                purchase_order_id=purchase_order_id,
                invoice_status=MATCHED,
                last_match_outcome=MATCHED_WITH_WARNING,
                match_status=MATCHED_WITH_WARNING,
                invoice_amount=invoice_amount,
                received_value=receipt_snapshot.received_value,
                ordered_value=receipt_snapshot.ordered_value,
                difference_amount=difference_amount,
                remaining_order_value=remaining_order_value,
                all_lines_fully_received=False,
                open_lines=receipt_snapshot.open_lines,
                next_action=PROCEED_TO_APPROVAL,
                evaluated_at=evaluated_at,
                purchase_order_status=receipt_snapshot.purchase_order_status,
                matched_at=matched_at,
                warning=warning,
                idempotency_key=idempotency_key,
            )

        return InvoiceMatchResult(
            snapshot_id=snapshot_id,
            invoice_id=invoice_id,
            purchase_order_id=purchase_order_id,
            invoice_status=MATCHED,
            last_match_outcome=MATCHED_CLEAN,
            match_status=MATCHED_CLEAN,
            invoice_amount=invoice_amount,
            received_value=receipt_snapshot.received_value,
            ordered_value=receipt_snapshot.ordered_value,
            difference_amount=difference_amount,
            remaining_order_value=remaining_order_value,
            all_lines_fully_received=True,
            open_lines=[],
            next_action=PROCEED_TO_APPROVAL,
            evaluated_at=evaluated_at,
            purchase_order_status=receipt_snapshot.purchase_order_status,
            matched_at=matched_at,
            idempotency_key=idempotency_key,
        )