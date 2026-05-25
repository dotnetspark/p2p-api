from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.persistence.database import Base


class GLEntryRow(Base):
    __tablename__ = "gl_entries"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    invoice_id: Mapped[str] = mapped_column(ForeignKey("invoices.id"), nullable=False, index=True)
    account_code: Mapped[str] = mapped_column(String(64), nullable=False)
    debit: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    credit: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    posted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    invoice = relationship("InvoiceRow", back_populates="gl_entries")