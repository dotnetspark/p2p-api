from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.persistence.database import Base


class InvoiceRow(Base):
    __tablename__ = "invoices"
    __table_args__ = (
        UniqueConstraint("vendor_id", "invoice_number", name="uq_invoices_vendor_invoice_number"),
    )

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    vendor_id: Mapped[str] = mapped_column(ForeignKey("vendors.id"), nullable=False, index=True)
    po_id: Mapped[str] = mapped_column(String(32), nullable=False, unique=True, index=True)
    invoice_number: Mapped[str] = mapped_column(String(64), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    last_match_outcome: Mapped[str] = mapped_column(String(24), nullable=False, default="NONE")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    matched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    vendor = relationship("VendorRow", back_populates="invoices")
    match_snapshots = relationship(
        "InvoiceMatchSnapshotRow",
        back_populates="invoice",
        cascade="all, delete-orphan",
    )
