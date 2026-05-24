from __future__ import annotations

from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from src.domain.models.goods_receipt import GoodsReceiptLineRecord, GoodsReceiptRecord
from src.persistence.models.goods_receipt import GoodsReceiptLineRow, GoodsReceiptRow


class GoodsReceiptRepository:
    def get_by_idempotency_key(
        self,
        session: Session,
        purchase_order_id: str,
        idempotency_key: str,
    ) -> GoodsReceiptRecord | None:
        stmt = (
            select(GoodsReceiptRow)
            .options(selectinload(GoodsReceiptRow.line_items))
            .where(GoodsReceiptRow.po_id == purchase_order_id)
            .where(GoodsReceiptRow.idempotency_key == idempotency_key)
        )
        row = session.execute(stmt).scalar_one_or_none()
        if row is None:
            return None
        return GoodsReceiptRecord(
            id=row.id,
            po_id=row.po_id,
            received_by=row.received_by,
            received_at=row.received_at,
            idempotency_key=row.idempotency_key,
            line_items=[
                GoodsReceiptLineRecord(
                    po_line_item_id=line_item_row.po_line_item_id,
                    qty_received=line_item_row.qty_received,
                )
                for line_item_row in sorted(row.line_items, key=lambda item: item.id)
            ],
        )

    def add(self, session: Session, receipt: GoodsReceiptRecord) -> GoodsReceiptRecord:
        row = GoodsReceiptRow(
            id=receipt.id,
            po_id=receipt.po_id,
            received_by=receipt.received_by,
            received_at=receipt.received_at,
            idempotency_key=receipt.idempotency_key,
        )
        row.line_items = [
            GoodsReceiptLineRow(
                id=f"GRL-{uuid4().hex[:10].upper()}",
                goods_receipt_id=receipt.id,
                po_line_item_id=line_item.po_line_item_id,
                qty_received=line_item.qty_received,
            )
            for line_item in receipt.line_items
        ]
        session.add(row)
        session.flush()
        return receipt