from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.persistence.database import Base


class InvoiceMatchSnapshotRow(Base):
    __tablename__ = "invoice_match_snapshots"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    invoice_id: Mapped[str] = mapped_column(ForeignKey("invoices.id"), nullable=False, index=True)
    idempotency_key: Mapped[str] = mapped_column(String(128), nullable=False, unique=True, index=True)
    outcome: Mapped[str] = mapped_column(String(24), nullable=False)
    invoice_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    received_value: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    ordered_value: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    difference_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    shortfall_amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    next_action: Mapped[str] = mapped_column(String(24), nullable=False)
    all_lines_fully_received: Mapped[bool] = mapped_column(Boolean, nullable=False)
    warning_code: Mapped[str | None] = mapped_column(String(32), nullable=True)
    remaining_order_value: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    purchase_order_status: Mapped[str] = mapped_column(String(16), nullable=False)
    open_lines_json: Mapped[str] = mapped_column(Text, nullable=False)
    evaluated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    matched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    invoice = relationship("InvoiceRow", back_populates="match_snapshots")