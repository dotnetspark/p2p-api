from __future__ import annotations

from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.persistence.database import Base


class InvoiceRow(Base):
    __tablename__ = "invoices"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    vendor_id: Mapped[str] = mapped_column(ForeignKey("vendors.id"), nullable=False, index=True)
    po_id: Mapped[str] = mapped_column(String(32), nullable=False)
    invoice_number: Mapped[str] = mapped_column(String(64), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, index=True)

    vendor = relationship("VendorRow", back_populates="invoices")
