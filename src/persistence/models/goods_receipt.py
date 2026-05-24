from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.persistence.database import Base


class GoodsReceiptRow(Base):
    __tablename__ = "goods_receipts"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    po_id: Mapped[str] = mapped_column(ForeignKey("purchase_orders.id"), nullable=False, index=True)
    received_by: Mapped[str] = mapped_column(String(128), nullable=False)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(128), nullable=False, unique=True, index=True)

    purchase_order = relationship("PurchaseOrderRow", back_populates="receipts")
    line_items = relationship(
        "GoodsReceiptLineRow",
        back_populates="goods_receipt",
        cascade="all, delete-orphan",
    )


class GoodsReceiptLineRow(Base):
    __tablename__ = "goods_receipt_line_items"

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    goods_receipt_id: Mapped[str] = mapped_column(ForeignKey("goods_receipts.id"), nullable=False, index=True)
    po_line_item_id: Mapped[str] = mapped_column(ForeignKey("purchase_order_line_items.id"), nullable=False, index=True)
    qty_received: Mapped[int] = mapped_column(Integer, nullable=False)

    goods_receipt = relationship("GoodsReceiptRow", back_populates="line_items")
    purchase_order_line_item = relationship("PurchaseOrderLineRow", back_populates="receipt_line_items")