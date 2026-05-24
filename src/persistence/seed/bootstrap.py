from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.persistence.models.invoice import InvoiceRow
from src.persistence.models.invoice_match_snapshot import InvoiceMatchSnapshotRow
from src.persistence.models.goods_receipt import GoodsReceiptLineRow, GoodsReceiptRow
from src.persistence.models.idempotency import IdempotencyKeyRow
from src.persistence.models.purchase_order import PurchaseOrderLineRow, PurchaseOrderRow
from src.persistence.models.vendor import VendorRow


def seed_initial_data(session: Session) -> None:
    existing_vendor = session.execute(select(VendorRow.id).limit(1)).scalar_one_or_none()
    if existing_vendor:
        return

    created_at = datetime.now(UTC)

    vendors = [
        VendorRow(id="V-100", name="ACME Building Supply", payment_terms="NET30", is_active=True),
        VendorRow(id="V-200", name="Beacon Aggregates", payment_terms="NET60", is_active=True),
        VendorRow(id="V-300", name="Dormant Timber Co", payment_terms="NET30", is_active=False),
    ]
    purchase_orders = [
        PurchaseOrderRow(
            id="PO-200",
            vendor_id="V-100",
            status="SUBMITTED",
            created_at=created_at,
            submitted_at=created_at,
            create_idempotency_key=None,
            submit_idempotency_key=None,
            invoice_id=None,
        )
    ]
    purchase_order_lines = [
        PurchaseOrderLineRow(
            id="POL-200-01",
            po_id="PO-200",
            sku="SKU-INV-1000",
            description="Invoice Matching Seed Item",
            qty_ordered=100,
            qty_received=60,
            unit_cost=Decimal("10.00"),
        )
    ]
    goods_receipts = [
        GoodsReceiptRow(
            id="GR-200-01",
            po_id="PO-200",
            received_by="seed-loader",
            received_at=created_at,
            idempotency_key="seed-gr-200-01",
        )
    ]
    goods_receipt_lines = [
        GoodsReceiptLineRow(
            id="GRL-200-01",
            goods_receipt_id="GR-200-01",
            po_line_item_id="POL-200-01",
            qty_received=60,
        )
    ]
    invoices = [
        InvoiceRow(id="INV-1001", vendor_id="V-100", po_id="PO-1001", invoice_number="A1001", amount=Decimal("1250.00"), status="PENDING", last_match_outcome="NONE", created_at=created_at, matched_at=None),
        InvoiceRow(id="INV-1002", vendor_id="V-100", po_id="PO-1002", invoice_number="A1002", amount=Decimal("500.00"), status="APPROVED", last_match_outcome="MATCHED", created_at=created_at, matched_at=created_at),
        InvoiceRow(id="INV-1003", vendor_id="V-100", po_id="PO-1003", invoice_number="A1003", amount=Decimal("99.99"), status="PAID", last_match_outcome="MATCHED", created_at=created_at, matched_at=created_at),
        InvoiceRow(id="INV-2001", vendor_id="V-300", po_id="PO-2001", invoice_number="D2001", amount=Decimal("300.00"), status="MATCHED", last_match_outcome="MATCHED", created_at=created_at, matched_at=created_at),
    ]
    session.add_all(vendors + purchase_orders + purchase_order_lines + goods_receipts + goods_receipt_lines + invoices)
    session.commit()
