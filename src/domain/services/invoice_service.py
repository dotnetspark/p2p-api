from __future__ import annotations

from decimal import Decimal

from sqlalchemy.orm import Session

from src.core.errors import (
    ServiceError,
    dependency_temporarily_unavailable,
    idempotency_key_conflict,
    invoice_duplicate_reference,
    invoice_vendor_po_mismatch,
    purchase_order_invalid_state,
    purchase_order_not_found,
    vendor_not_found,
)
from src.core.idempotency import build_idempotency_fingerprint
from src.core.results import Result
from src.domain.models.invoice import InvoiceCreateResult, build_pending_invoice
from src.domain.services.vendor_credit_alert_service import VendorCreditAlertService
from src.persistence.repositories.idempotency_repository import IdempotencyRepository
from src.persistence.repositories.credit_check_repository import CreditCheckRepository
from src.persistence.repositories.invoice_repository import InvoiceRepository
from src.persistence.repositories.purchase_order_repository import PurchaseOrderRepository
from src.persistence.repositories.vendor_repository import VendorRepository


CREATE_INVOICE_OPERATION = "invoice.create"


class InvoiceService:
    def __init__(
        self,
        vendor_repository: VendorRepository | None = None,
        purchase_order_repository: PurchaseOrderRepository | None = None,
        invoice_repository: InvoiceRepository | None = None,
        idempotency_repository: IdempotencyRepository | None = None,
        credit_check_repository: CreditCheckRepository | None = None,
        vendor_credit_alert_service: VendorCreditAlertService | None = None,
    ) -> None:
        self.vendor_repository = vendor_repository or VendorRepository()
        self.purchase_order_repository = purchase_order_repository or PurchaseOrderRepository()
        self.invoice_repository = invoice_repository or InvoiceRepository()
        self.idempotency_repository = idempotency_repository or IdempotencyRepository()
        self.credit_check_repository = credit_check_repository or CreditCheckRepository()
        self.vendor_credit_alert_service = vendor_credit_alert_service or VendorCreditAlertService(
            credit_check_repository=self.credit_check_repository,
            invoice_repository=self.invoice_repository,
            vendor_repository=self.vendor_repository,
        )

    def create_invoice(
        self,
        session: Session,
        vendor_id: str,
        purchase_order_id: str,
        invoice_number: str,
        invoice_amount: Decimal,
        idempotency_key: str,
        correlation_id: str,
    ) -> Result[InvoiceCreateResult, ServiceError]:
        normalized_amount = invoice_amount.quantize(Decimal("0.01"))
        request_fingerprint = build_idempotency_fingerprint(
            CREATE_INVOICE_OPERATION,
            {
                "vendor_id": vendor_id,
                "purchase_order_id": purchase_order_id,
                "invoice_number": invoice_number,
                "invoice_amount": normalized_amount,
            },
        )
        idempotency_result = self._resolve_idempotency(
            session=session,
            idempotency_key=idempotency_key,
            request_fingerprint=request_fingerprint,
        )
        if idempotency_result is not None:
            return idempotency_result

        vendor = self.vendor_repository.get_by_id(session, vendor_id)
        if vendor is None:
            return Result.fail(vendor_not_found(vendor_id))

        purchase_order = self.purchase_order_repository.get_by_id(session, purchase_order_id)
        if purchase_order is None:
            return Result.fail(purchase_order_not_found(purchase_order_id))
        if purchase_order.vendor_id != vendor_id:
            return Result.fail(invoice_vendor_po_mismatch(vendor_id, purchase_order_id))
        if purchase_order.invoice_id is not None:
            return Result.fail(
                purchase_order_invalid_state(
                    purchase_order_id,
                    purchase_order.status,
                    "NO_INVOICE",
                    "invoice registration",
                )
            )

        existing_invoice = self.invoice_repository.get_by_vendor_and_invoice_number(
            session,
            vendor_id,
            invoice_number,
        )
        if existing_invoice is not None:
            return Result.fail(invoice_duplicate_reference(vendor_id, invoice_number))

        invoice = build_pending_invoice(
            vendor_id=vendor_id,
            purchase_order_id=purchase_order_id,
            invoice_number=invoice_number,
            invoice_amount=normalized_amount,
        )
        try:
            self.invoice_repository.add(session, invoice)
            self.purchase_order_repository.assign_invoice(session, purchase_order_id, invoice.id)
            credit_check = self.vendor_credit_alert_service.create_pending_for_invoice_create(
                session=session,
                vendor_id=vendor_id,
                invoice_id=invoice.id,
                correlation_id=correlation_id,
                idempotency_key=idempotency_key,
            )
            self.idempotency_repository.add(
                session,
                key=idempotency_key,
                operation=CREATE_INVOICE_OPERATION,
                request_fingerprint=request_fingerprint,
                resource_id=invoice.id,
                credit_check_id=credit_check.id,
            )
            session.commit()
        except Exception:
            session.rollback()
            return Result.fail(dependency_temporarily_unavailable())
        return Result.ok(
            InvoiceCreateResult(
                invoice=invoice,
                credit_check_id=credit_check.id,
                should_schedule_credit_check=True,
            )
        )

    def _resolve_idempotency(
        self,
        session: Session,
        idempotency_key: str,
        request_fingerprint: str,
    ) -> Result[InvoiceCreateResult, ServiceError] | None:
        existing_record = self.idempotency_repository.get_by_key(session, idempotency_key)
        if existing_record is None:
            return None
        if (
            existing_record.operation != CREATE_INVOICE_OPERATION
            or existing_record.request_fingerprint != request_fingerprint
        ):
            return Result.fail(idempotency_key_conflict(idempotency_key))
        existing_invoice = self.invoice_repository.get_by_id(session, existing_record.resource_id)
        if existing_invoice is None:
            return Result.fail(dependency_temporarily_unavailable())
        credit_check_id = existing_record.credit_check_id
        if credit_check_id is None:
            credit_check = self.credit_check_repository.get_by_idempotency_key(
                session,
                idempotency_key,
                "CREATE",
            )
            if credit_check is None:
                return Result.fail(dependency_temporarily_unavailable())
            credit_check_id = credit_check.id
        return Result.ok(
            InvoiceCreateResult(
                invoice=existing_invoice,
                credit_check_id=credit_check_id,
                should_schedule_credit_check=False,
            )
        )