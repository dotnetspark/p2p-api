from __future__ import annotations

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.persistence.models.invoice import InvoiceRow
from src.persistence.models.vendor import VendorRow


def seed_initial_data(session: Session) -> None:
    existing_vendor = session.execute(select(VendorRow.id).limit(1)).scalar_one_or_none()
    if existing_vendor:
        return

    vendors = [
        VendorRow(id="V-100", name="ACME Building Supply", payment_terms="NET30", is_active=True),
        VendorRow(id="V-200", name="Beacon Aggregates", payment_terms="NET60", is_active=True),
        VendorRow(id="V-300", name="Dormant Timber Co", payment_terms="NET30", is_active=False),
    ]
    invoices = [
        InvoiceRow(id="INV-1001", vendor_id="V-100", po_id="PO-1001", invoice_number="A1001", amount=Decimal("1250.00"), status="PENDING"),
        InvoiceRow(id="INV-1002", vendor_id="V-100", po_id="PO-1002", invoice_number="A1002", amount=Decimal("500.00"), status="APPROVED"),
        InvoiceRow(id="INV-1003", vendor_id="V-100", po_id="PO-1003", invoice_number="A1003", amount=Decimal("99.99"), status="PAID"),
        InvoiceRow(id="INV-2001", vendor_id="V-300", po_id="PO-2001", invoice_number="D2001", amount=Decimal("300.00"), status="MATCHED"),
    ]
    session.add_all(vendors + invoices)
    session.commit()
