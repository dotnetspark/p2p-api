from __future__ import annotations

from decimal import Decimal
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from src.domain.models.goods_receipt import GoodsReceiptLineRecord, GoodsReceiptRecord
from src.domain.models.purchase_order import PurchaseOrder, PurchaseOrderLineItem
from src.persistence.models.goods_receipt import GoodsReceiptRow
from src.persistence.models.purchase_order import PurchaseOrderLineRow, PurchaseOrderRow


class PurchaseOrderRepository:
    def get_by_id(self, session: Session, purchase_order_id: str) -> PurchaseOrder | None:
        stmt = (
            select(PurchaseOrderRow)
            .options(
                selectinload(PurchaseOrderRow.line_items),
                selectinload(PurchaseOrderRow.receipts).selectinload(GoodsReceiptRow.line_items),
            )
            .where(PurchaseOrderRow.id == purchase_order_id)
        )
        row = session.execute(stmt).scalar_one_or_none()
        if row is None:
            return None
        return self._to_domain(row)

    def get_by_create_idempotency_key(self, session: Session, idempotency_key: str) -> PurchaseOrder | None:
        stmt = (
            select(PurchaseOrderRow)
            .options(
                selectinload(PurchaseOrderRow.line_items),
                selectinload(PurchaseOrderRow.receipts).selectinload(GoodsReceiptRow.line_items),
            )
            .where(PurchaseOrderRow.create_idempotency_key == idempotency_key)
        )
        row = session.execute(stmt).scalar_one_or_none()
        if row is None:
            return None
        return self._to_domain(row)

    def add(self, session: Session, purchase_order: PurchaseOrder) -> PurchaseOrder:
        row = PurchaseOrderRow(
            id=purchase_order.id,
            vendor_id=purchase_order.vendor_id,
            status=purchase_order.status,
            created_at=purchase_order.created_at,
            submitted_at=purchase_order.submitted_at,
            create_idempotency_key=purchase_order.create_idempotency_key,
            submit_idempotency_key=purchase_order.submit_idempotency_key,
            invoice_id=purchase_order.invoice_id,
        )
        row.line_items = [
            PurchaseOrderLineRow(
                id=line_item.id,
                po_id=purchase_order.id,
                sku=line_item.sku,
                description=line_item.description,
                qty_ordered=line_item.qty_ordered,
                qty_received=line_item.qty_received,
                unit_cost=line_item.unit_cost,
            )
            for line_item in purchase_order.line_items
        ]
        session.add(row)
        session.flush()
        return purchase_order

    def update(self, session: Session, purchase_order: PurchaseOrder) -> PurchaseOrder:
        row = session.get(PurchaseOrderRow, purchase_order.id)
        if row is None:
            raise ValueError(f"Purchase order {purchase_order.id} not found for update.")

        row.status = purchase_order.status
        row.submitted_at = purchase_order.submitted_at
        row.submit_idempotency_key = purchase_order.submit_idempotency_key
        row.invoice_id = purchase_order.invoice_id

        line_items_by_id = {line_item.id: line_item for line_item in purchase_order.line_items}
        for line_row in row.line_items:
            domain_line = line_items_by_id[line_row.id]
            line_row.qty_received = domain_line.qty_received
        session.flush()
        return purchase_order

    def _to_domain(self, row: PurchaseOrderRow) -> PurchaseOrder:
        line_items = [
            PurchaseOrderLineItem(
                id=line_row.id,
                sku=line_row.sku,
                description=line_row.description,
                qty_ordered=line_row.qty_ordered,
                qty_received=line_row.qty_received,
                unit_cost=Decimal(line_row.unit_cost).quantize(Decimal("0.01")),
            )
            for line_row in sorted(row.line_items, key=lambda item: item.id)
        ]
        receipts = []
        for receipt_row in sorted(row.receipts, key=lambda item: (self._normalize_datetime(item.received_at), item.id)):
            receipt_line_items = [
                GoodsReceiptLineRecord(
                    po_line_item_id=line_row.po_line_item_id,
                    qty_received=line_row.qty_received,
                )
                for line_row in sorted(receipt_row.line_items, key=lambda item: item.id)
            ]
            receipts.append(
                GoodsReceiptRecord(
                    id=receipt_row.id,
                    po_id=receipt_row.po_id,
                    received_by=receipt_row.received_by,
                    received_at=receipt_row.received_at,
                    idempotency_key=receipt_row.idempotency_key,
                    line_items=receipt_line_items,
                )
            )
        return PurchaseOrder(
            id=row.id,
            vendor_id=row.vendor_id,
            status=row.status,
            created_at=row.created_at,
            submitted_at=row.submitted_at,
            line_items=line_items,
            receipts=receipts,
            create_idempotency_key=row.create_idempotency_key,
            submit_idempotency_key=row.submit_idempotency_key,
            invoice_id=row.invoice_id,
        )

    @staticmethod
    def _normalize_datetime(value: datetime) -> datetime:
        return value.replace(tzinfo=None) if value.tzinfo is not None else value