from __future__ import annotations

from sqlalchemy.orm import Session

from src.core.errors import (
    ServiceError,
    dependency_temporarily_unavailable,
    idempotency_key_conflict,
    purchase_order_not_found,
)
from src.core.idempotency import build_idempotency_fingerprint
from src.core.results import Result
from src.domain.models.goods_receipt import GoodsReceiptLineInput
from src.domain.models.purchase_order import PurchaseOrder, apply_goods_receipt
from src.persistence.repositories.idempotency_repository import IdempotencyRepository
from src.persistence.repositories.goods_receipt_repository import GoodsReceiptRepository
from src.persistence.repositories.purchase_order_repository import PurchaseOrderRepository


RECEIVE_GOODS_OPERATION = "purchase_order.receive"


class GoodsReceiptService:
    def __init__(
        self,
        purchase_order_repository: PurchaseOrderRepository | None = None,
        goods_receipt_repository: GoodsReceiptRepository | None = None,
        idempotency_repository: IdempotencyRepository | None = None,
    ) -> None:
        self.purchase_order_repository = purchase_order_repository or PurchaseOrderRepository()
        self.goods_receipt_repository = goods_receipt_repository or GoodsReceiptRepository()
        self.idempotency_repository = idempotency_repository or IdempotencyRepository()

    def receive_goods(
        self,
        session: Session,
        purchase_order_id: str,
        received_by: str,
        line_items: list[GoodsReceiptLineInput],
        idempotency_key: str,
    ) -> Result[PurchaseOrder, ServiceError]:
        request_fingerprint = build_idempotency_fingerprint(
            RECEIVE_GOODS_OPERATION,
            {
                "purchase_order_id": purchase_order_id,
                "received_by": received_by,
                "line_items": self._normalize_line_items(line_items),
            },
        )
        existing_record = self.idempotency_repository.get_by_key(session, idempotency_key)
        if existing_record is not None:
            if (
                existing_record.operation != RECEIVE_GOODS_OPERATION
                or existing_record.request_fingerprint != request_fingerprint
            ):
                return Result.fail(idempotency_key_conflict(idempotency_key))
            existing_purchase_order = self.purchase_order_repository.get_by_id(session, existing_record.resource_id)
            if existing_purchase_order is None:
                return Result.fail(dependency_temporarily_unavailable())
            return Result.ok(existing_purchase_order)

        existing_receipt = self.goods_receipt_repository.get_by_idempotency_key(session, purchase_order_id, idempotency_key)
        if existing_receipt is not None:
            existing_purchase_order = self.purchase_order_repository.get_by_id(session, purchase_order_id)
            if existing_purchase_order is not None:
                return Result.ok(existing_purchase_order)

        purchase_order = self.purchase_order_repository.get_by_id(session, purchase_order_id)
        if purchase_order is None:
            return Result.fail(purchase_order_not_found(purchase_order_id))

        receipt_result = apply_goods_receipt(
            purchase_order=purchase_order,
            received_by=received_by,
            line_items=line_items,
            idempotency_key=idempotency_key,
        )
        if receipt_result.error is not None:
            return Result.fail(receipt_result.error)

        updated_purchase_order, receipt_record = receipt_result.value
        try:
            self.purchase_order_repository.update(session, updated_purchase_order)
            self.goods_receipt_repository.add(session, receipt_record)
            self.idempotency_repository.add(
                session,
                key=idempotency_key,
                operation=RECEIVE_GOODS_OPERATION,
                request_fingerprint=request_fingerprint,
                resource_id=updated_purchase_order.id,
            )
            session.commit()
        except Exception:
            session.rollback()
            return Result.fail(dependency_temporarily_unavailable())
        refreshed_purchase_order = self.purchase_order_repository.get_by_id(session, purchase_order_id)
        return Result.ok(refreshed_purchase_order or updated_purchase_order)

    @staticmethod
    def _normalize_line_items(line_items: list[GoodsReceiptLineInput]) -> list[dict[str, int | str]]:
        aggregated_quantities: dict[str, int] = {}
        for line_item in line_items:
            aggregated_quantities[line_item.po_line_item_id] = (
                aggregated_quantities.get(line_item.po_line_item_id, 0) + line_item.qty_received
            )
        return [
            {"po_line_item_id": po_line_item_id, "qty_received": qty_received}
            for po_line_item_id, qty_received in sorted(aggregated_quantities.items())
        ]