from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

from src.core.errors import (
    ServiceError,
    purchase_order_invalid_state,
    purchase_order_line_invalid,
    purchase_order_over_receipt,
)
from src.core.results import Result
from src.domain.models.goods_receipt import GoodsReceiptLineInput, GoodsReceiptLineRecord, GoodsReceiptRecord


DRAFT = "DRAFT"
SUBMITTED = "SUBMITTED"
RECEIVED = "RECEIVED"
CLOSED = "CLOSED"


@dataclass(frozen=True)
class PurchaseOrderLineInput:
    sku: str
    description: str
    qty_ordered: int
    unit_cost: Decimal


@dataclass(frozen=True)
class PurchaseOrderLineItem:
    id: str
    sku: str
    description: str
    qty_ordered: int
    qty_received: int
    unit_cost: Decimal

    @property
    def qty_remaining(self) -> int:
        return self.qty_ordered - self.qty_received


@dataclass(frozen=True)
class PurchaseOrder:
    id: str
    vendor_id: str
    status: str
    created_at: datetime
    submitted_at: datetime | None
    line_items: list[PurchaseOrderLineItem]
    receipts: list[GoodsReceiptRecord]
    create_idempotency_key: str | None = None
    submit_idempotency_key: str | None = None
    invoice_id: str | None = None


def validate_purchase_order_line_inputs(line_items: list[PurchaseOrderLineInput]) -> ServiceError | None:
    if not line_items:
        return purchase_order_line_invalid("Purchase orders must contain at least one line item.")

    for index, line_item in enumerate(line_items, start=1):
        if line_item.qty_ordered <= 0:
            return purchase_order_line_invalid(
                f"Line item {index} must have a quantity greater than zero."
            )
        if line_item.unit_cost <= Decimal("0"):
            return purchase_order_line_invalid(
                f"Line item {index} must have a unit cost greater than zero."
            )
    return None


def build_draft_purchase_order(
    vendor_id: str,
    line_items: list[PurchaseOrderLineInput],
    create_idempotency_key: str,
    created_at: datetime | None = None,
) -> PurchaseOrder:
    created_timestamp = created_at or datetime.now(UTC)
    po_suffix = uuid4().hex[:8].upper()
    purchase_order_id = f"PO-{po_suffix}"
    normalized_line_items = [
        PurchaseOrderLineItem(
            id=f"POL-{po_suffix}-{index:02d}",
            sku=line_item.sku,
            description=line_item.description,
            qty_ordered=line_item.qty_ordered,
            qty_received=0,
            unit_cost=line_item.unit_cost.quantize(Decimal("0.01")),
        )
        for index, line_item in enumerate(line_items, start=1)
    ]
    return PurchaseOrder(
        id=purchase_order_id,
        vendor_id=vendor_id,
        status=DRAFT,
        created_at=created_timestamp,
        submitted_at=None,
        line_items=normalized_line_items,
        receipts=[],
        create_idempotency_key=create_idempotency_key,
    )


def submit_purchase_order(
    purchase_order: PurchaseOrder,
    submit_idempotency_key: str,
    submitted_at: datetime | None = None,
) -> Result[PurchaseOrder, ServiceError]:
    if purchase_order.status != DRAFT:
        return Result.fail(
            purchase_order_invalid_state(
                purchase_order.id,
                purchase_order.status,
                DRAFT,
                "submission",
            )
        )

    return Result.ok(
        replace(
            purchase_order,
            status=SUBMITTED,
            submitted_at=submitted_at or datetime.now(UTC),
            submit_idempotency_key=submit_idempotency_key,
        )
    )


def apply_goods_receipt(
    purchase_order: PurchaseOrder,
    received_by: str,
    line_items: list[GoodsReceiptLineInput],
    idempotency_key: str,
    received_at: datetime | None = None,
) -> Result[tuple[PurchaseOrder, GoodsReceiptRecord], ServiceError]:
    if purchase_order.status != SUBMITTED:
        return Result.fail(
            purchase_order_invalid_state(
                purchase_order.id,
                purchase_order.status,
                SUBMITTED,
                "receiving goods",
            )
        )

    if not line_items:
        return Result.fail(purchase_order_line_invalid("Goods receipts must contain at least one line item."))

    aggregated_receipt_quantities: dict[str, int] = {}
    for line_item in line_items:
        if line_item.qty_received <= 0:
            return Result.fail(purchase_order_line_invalid("Goods receipt quantities must be greater than zero."))
        aggregated_receipt_quantities[line_item.po_line_item_id] = (
            aggregated_receipt_quantities.get(line_item.po_line_item_id, 0) + line_item.qty_received
        )

    order_line_items_by_id = {line_item.id: line_item for line_item in purchase_order.line_items}
    updated_line_items: list[PurchaseOrderLineItem] = []
    receipt_line_records: list[GoodsReceiptLineRecord] = []

    for existing_line_item in purchase_order.line_items:
        additional_quantity = aggregated_receipt_quantities.pop(existing_line_item.id, 0)
        if existing_line_item.id not in order_line_items_by_id:
            return Result.fail(
                purchase_order_line_invalid(
                    f"Goods receipt references unknown purchase order line {existing_line_item.id}."
                )
            )
        new_received_total = existing_line_item.qty_received + additional_quantity
        if new_received_total > existing_line_item.qty_ordered:
            return Result.fail(
                purchase_order_over_receipt(
                    existing_line_item.id,
                    existing_line_item.qty_ordered,
                    existing_line_item.qty_received,
                    additional_quantity,
                )
            )
        updated_line_items.append(replace(existing_line_item, qty_received=new_received_total))
        if additional_quantity > 0:
            receipt_line_records.append(
                GoodsReceiptLineRecord(
                    po_line_item_id=existing_line_item.id,
                    qty_received=additional_quantity,
                )
            )

    if aggregated_receipt_quantities:
        unknown_line_item_id = next(iter(aggregated_receipt_quantities.keys()))
        return Result.fail(
            purchase_order_line_invalid(
                f"Goods receipt references unknown purchase order line {unknown_line_item_id}."
            )
        )

    receipt_timestamp = received_at or datetime.now(UTC)
    receipt_record = GoodsReceiptRecord(
        id=f"GR-{uuid4().hex[:8].upper()}",
        po_id=purchase_order.id,
        received_by=received_by,
        received_at=receipt_timestamp,
        idempotency_key=idempotency_key,
        line_items=receipt_line_records,
    )
    next_status = RECEIVED if all(line_item.qty_received == line_item.qty_ordered for line_item in updated_line_items) else SUBMITTED
    updated_purchase_order = replace(
        purchase_order,
        status=next_status,
        line_items=updated_line_items,
        receipts=[*purchase_order.receipts, receipt_record],
    )
    return Result.ok((updated_purchase_order, receipt_record))