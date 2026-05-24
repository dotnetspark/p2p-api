from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.persistence.database import Base


class PurchaseOrderRow(Base):
    __tablename__ = "purchase_orders"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    vendor_id: Mapped[str] = mapped_column(ForeignKey("vendors.id"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    create_idempotency_key: Mapped[str | None] = mapped_column(String(128), nullable=True, unique=True, index=True)
    submit_idempotency_key: Mapped[str | None] = mapped_column(String(128), nullable=True)
    invoice_id: Mapped[str | None] = mapped_column(String(32), nullable=True, unique=True)

    line_items = relationship(
        "PurchaseOrderLineRow",
        back_populates="purchase_order",
        cascade="all, delete-orphan",
    )
    receipts = relationship(
        "GoodsReceiptRow",
        back_populates="purchase_order",
        cascade="all, delete-orphan",
    )


class PurchaseOrderLineRow(Base):
    __tablename__ = "purchase_order_line_items"

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    po_id: Mapped[str] = mapped_column(ForeignKey("purchase_orders.id"), nullable=False, index=True)
    sku: Mapped[str] = mapped_column(String(64), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    qty_ordered: Mapped[int] = mapped_column(Integer, nullable=False)
    qty_received: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    unit_cost: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    purchase_order = relationship("PurchaseOrderRow", back_populates="line_items")
    receipt_line_items = relationship("GoodsReceiptLineRow", back_populates="purchase_order_line_item")