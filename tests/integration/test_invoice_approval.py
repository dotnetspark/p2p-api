from __future__ import annotations

from src.persistence.database import get_session_factory
from src.persistence.models.gl_entry import GLEntryRow
from src.persistence.models.invoice import InvoiceRow


def _create_submitted_purchase_order(client, suffix: str) -> tuple[str, str]:
    create = client.post(
        "/purchase-orders",
        headers={"X-Correlation-ID": f"it-approve-po-create-{suffix}", "Idempotency-Key": f"it-approve-po-create-{suffix}"},
        json={
            "vendor_id": "V-100",
            "line_items": [
                {
                    "sku": f"SKU-APPROVE-{suffix}",
                    "description": f"Approval Item {suffix}",
                    "qty_ordered": 100,
                    "unit_cost": "10.00",
                }
            ],
        },
    )
    assert create.status_code == 201
    purchase_order_id = create.json()["purchase_order_id"]
    po_line_item_id = create.json()["line_items"][0]["po_line_item_id"]
    submit = client.post(
        f"/purchase-orders/{purchase_order_id}/submit",
        headers={"X-Correlation-ID": f"it-approve-po-submit-{suffix}", "Idempotency-Key": f"it-approve-po-submit-{suffix}"},
    )
    assert submit.status_code == 200
    return purchase_order_id, po_line_item_id


def _receive_goods(client, purchase_order_id: str, po_line_item_id: str, suffix: str, qty_received: int) -> None:
    response = client.post(
        f"/purchase-orders/{purchase_order_id}/receive",
        headers={"X-Correlation-ID": f"it-approve-receive-{suffix}", "Idempotency-Key": f"it-approve-receive-{suffix}"},
        json={"received_by": "warehouse-agent", "line_items": [{"po_line_item_id": po_line_item_id, "qty_received": qty_received}]},
    )
    assert response.status_code == 200


def _create_invoice(client, purchase_order_id: str, suffix: str, invoice_amount: str) -> str:
    response = client.post(
        "/invoices",
        headers={"X-Correlation-ID": f"it-approve-invoice-create-{suffix}", "Idempotency-Key": f"it-approve-invoice-create-{suffix}"},
        json={
            "vendor_id": "V-100",
            "purchase_order_id": purchase_order_id,
            "invoice_number": f"INV-APPROVE-{suffix}",
            "invoice_amount": invoice_amount,
        },
    )
    assert response.status_code == 201
    return response.json()["invoice_id"]


def test_invoice_approval_integration_persists_balanced_gl_entries(client):
    purchase_order_id, po_line_item_id = _create_submitted_purchase_order(client, "persist")
    _receive_goods(client, purchase_order_id, po_line_item_id, "persist", 100)
    invoice_id = _create_invoice(client, purchase_order_id, "persist", "1000.00")
    match = client.post(
        f"/invoices/{invoice_id}/match",
        headers={"X-Correlation-ID": "it-invoice-approve-match", "Idempotency-Key": "it-invoice-approve-match"},
    )
    assert match.status_code == 200

    response = client.post(
        f"/invoices/{invoice_id}/approve",
        headers={"X-Correlation-ID": "it-invoice-approve-1", "Idempotency-Key": "it-invoice-approve-1"},
    )

    assert response.status_code == 200
    session = get_session_factory()()
    try:
        invoice_row = session.get(InvoiceRow, invoice_id)
        assert invoice_row is not None
        assert invoice_row.status == "APPROVED"
        assert invoice_row.approved_at is not None

        gl_entries = session.query(GLEntryRow).filter(GLEntryRow.invoice_id == invoice_id).order_by(GLEntryRow.id).all()
        assert len(gl_entries) == 2
        assert sum(entry.debit for entry in gl_entries) == sum(entry.credit for entry in gl_entries)
    finally:
        session.close()


def test_invoice_approval_integration_replay_does_not_duplicate_gl_entries(client):
    purchase_order_id, po_line_item_id = _create_submitted_purchase_order(client, "replay")
    _receive_goods(client, purchase_order_id, po_line_item_id, "replay", 100)
    invoice_id = _create_invoice(client, purchase_order_id, "replay", "1000.00")
    match = client.post(
        f"/invoices/{invoice_id}/match",
        headers={"X-Correlation-ID": "it-invoice-approve-replay-match", "Idempotency-Key": "it-invoice-approve-replay-match"},
    )
    assert match.status_code == 200

    first = client.post(
        f"/invoices/{invoice_id}/approve",
        headers={"X-Correlation-ID": "it-invoice-approve-replay-1", "Idempotency-Key": "it-invoice-approve-replay"},
    )
    replay = client.post(
        f"/invoices/{invoice_id}/approve",
        headers={"X-Correlation-ID": "it-invoice-approve-replay-2", "Idempotency-Key": "it-invoice-approve-replay"},
    )

    assert first.status_code == 200
    assert replay.status_code == 200
    session = get_session_factory()()
    try:
        gl_entries = session.query(GLEntryRow).filter(GLEntryRow.invoice_id == invoice_id).all()
        assert len(gl_entries) == 2
    finally:
        session.close()