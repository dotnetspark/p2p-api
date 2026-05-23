from __future__ import annotations

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.persistence.database import Base


class VendorRow(Base):
    __tablename__ = "vendors"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    payment_terms: Mapped[str] = mapped_column(String(16), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    invoices = relationship("InvoiceRow", back_populates="vendor", cascade="all, delete-orphan")
