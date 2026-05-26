from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.persistence.database import Base


class CreditAlertRow(Base):
    __tablename__ = "credit_alerts"
    __table_args__ = (
        UniqueConstraint("vendor_id", name="uq_credit_alerts_vendor_id"),
    )

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    vendor_id: Mapped[str] = mapped_column(ForeignKey("vendors.id"), nullable=False, index=True)
    credit_check_id: Mapped[str] = mapped_column(ForeignKey("credit_checks.id"), nullable=False, unique=True, index=True)
    triggering_invoice_id: Mapped[str] = mapped_column(ForeignKey("invoices.id"), nullable=False, index=True)
    outstanding_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    credit_limit: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    percentage_consumed: Mapped[float] = mapped_column(Numeric(8, 2), nullable=False)
    breached_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    advisory_only: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    vendor = relationship("VendorRow")
    invoice = relationship("InvoiceRow")
    credit_check = relationship("CreditCheckRow")