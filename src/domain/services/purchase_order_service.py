from __future__ import annotations

from sqlalchemy.orm import Session

from src.core.errors import (
    ServiceError,
    dependency_temporarily_unavailable,
    idempotency_key_conflict,
    purchase_order_not_found,
    vendor_inactive,
    vendor_not_found,
)
from src.core.idempotency import build_idempotency_fingerprint
from src.core.results import Result
from src.domain.models.purchase_order import (
    PurchaseOrder,
    PurchaseOrderLineInput,
    build_draft_purchase_order,
    submit_purchase_order,
    validate_purchase_order_line_inputs,
)
from src.persistence.repositories.idempotency_repository import IdempotencyRepository
from src.persistence.repositories.purchase_order_repository import PurchaseOrderRepository
from src.persistence.repositories.vendor_repository import VendorRepository


CREATE_PURCHASE_ORDER_OPERATION = "purchase_order.create"
SUBMIT_PURCHASE_ORDER_OPERATION = "purchase_order.submit"


class PurchaseOrderService:
    def __init__(
        self,
        vendor_repository: VendorRepository | None = None,
        purchase_order_repository: PurchaseOrderRepository | None = None,
        idempotency_repository: IdempotencyRepository | None = None,
    ) -> None:
        self.vendor_repository = vendor_repository or VendorRepository()
        self.purchase_order_repository = purchase_order_repository or PurchaseOrderRepository()
        self.idempotency_repository = idempotency_repository or IdempotencyRepository()

    def create_purchase_order(
        self,
        session: Session,
        vendor_id: str,
        line_items: list[PurchaseOrderLineInput],
        idempotency_key: str,
    ) -> Result[PurchaseOrder, ServiceError]:
        request_fingerprint = build_idempotency_fingerprint(
            CREATE_PURCHASE_ORDER_OPERATION,
            {
                "vendor_id": vendor_id,
                "line_items": line_items,
            },
        )
        idempotency_result = self._resolve_idempotency(
            session=session,
            idempotency_key=idempotency_key,
            operation=CREATE_PURCHASE_ORDER_OPERATION,
            request_fingerprint=request_fingerprint,
        )
        if idempotency_result is not None:
            return idempotency_result

        vendor = self.vendor_repository.get_by_id(session, vendor_id)
        if vendor is None:
            return Result.fail(vendor_not_found(vendor_id))
        if not vendor.is_active:
            return Result.fail(vendor_inactive(vendor_id))

        validation_error = validate_purchase_order_line_inputs(line_items)
        if validation_error is not None:
            return Result.fail(validation_error)

        purchase_order = build_draft_purchase_order(
            vendor_id=vendor_id,
            line_items=line_items,
            create_idempotency_key=idempotency_key,
        )
        try:
            self.purchase_order_repository.add(session, purchase_order)
            self.idempotency_repository.add(
                session,
                key=idempotency_key,
                operation=CREATE_PURCHASE_ORDER_OPERATION,
                request_fingerprint=request_fingerprint,
                resource_id=purchase_order.id,
            )
            session.commit()
        except Exception:
            session.rollback()
            return Result.fail(dependency_temporarily_unavailable())
        return Result.ok(purchase_order)

    def submit_purchase_order(
        self,
        session: Session,
        purchase_order_id: str,
        idempotency_key: str,
    ) -> Result[PurchaseOrder, ServiceError]:
        request_fingerprint = build_idempotency_fingerprint(
            SUBMIT_PURCHASE_ORDER_OPERATION,
            {"purchase_order_id": purchase_order_id},
        )
        idempotency_result = self._resolve_idempotency(
            session=session,
            idempotency_key=idempotency_key,
            operation=SUBMIT_PURCHASE_ORDER_OPERATION,
            request_fingerprint=request_fingerprint,
        )
        if idempotency_result is not None:
            return idempotency_result

        purchase_order = self.purchase_order_repository.get_by_id(session, purchase_order_id)
        if purchase_order is None:
            return Result.fail(purchase_order_not_found(purchase_order_id))
        if purchase_order.submit_idempotency_key == idempotency_key:
            return Result.ok(purchase_order)

        submission_result = submit_purchase_order(purchase_order, idempotency_key)
        if submission_result.error is not None:
            return Result.fail(submission_result.error)

        try:
            self.purchase_order_repository.update(session, submission_result.value)
            self.idempotency_repository.add(
                session,
                key=idempotency_key,
                operation=SUBMIT_PURCHASE_ORDER_OPERATION,
                request_fingerprint=request_fingerprint,
                resource_id=submission_result.value.id,
            )
            session.commit()
        except Exception:
            session.rollback()
            return Result.fail(dependency_temporarily_unavailable())
        refreshed_purchase_order = self.purchase_order_repository.get_by_id(session, purchase_order_id)
        return Result.ok(refreshed_purchase_order or submission_result.value)

    def get_purchase_order(self, session: Session, purchase_order_id: str) -> Result[PurchaseOrder, ServiceError]:
        purchase_order = self.purchase_order_repository.get_by_id(session, purchase_order_id)
        if purchase_order is None:
            return Result.fail(purchase_order_not_found(purchase_order_id))
        return Result.ok(purchase_order)

    def _resolve_idempotency(
        self,
        session: Session,
        idempotency_key: str,
        operation: str,
        request_fingerprint: str,
    ) -> Result[PurchaseOrder, ServiceError] | None:
        existing_record = self.idempotency_repository.get_by_key(session, idempotency_key)
        if existing_record is None:
            return None
        if (
            existing_record.operation != operation
            or existing_record.request_fingerprint != request_fingerprint
        ):
            return Result.fail(idempotency_key_conflict(idempotency_key))
        existing_purchase_order = self.purchase_order_repository.get_by_id(session, existing_record.resource_id)
        if existing_purchase_order is None:
            return Result.fail(dependency_temporarily_unavailable())
        return Result.ok(existing_purchase_order)