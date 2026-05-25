from __future__ import annotations

from src.persistence.database import get_session_factory
from src.persistence.models.invoice import InvoiceRow
from src.persistence.models.purchase_order import PurchaseOrderRow


def _create_submitted_purchase_order(client, suffix: str) -> tuple[str, str]:
    create = client.post(
        "/purchase-orders",
        headers={"X-Correlation-ID": f"it-pay-po-create-{suffix}", "Idempotency-Key": f"it-pay-po-create-{suffix}"},
        json={
            "vendor_id": "V-100",
            "line_items": [
                {
                    "sku": f"SKU-PAY-{suffix}",
                    "description": f"Payment Item {suffix}",
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
        headers={"X-Correlation-ID": f"it-pay-po-submit-{suffix}", "Idempotency-Key": f"it-pay-po-submit-{suffix}"},
    )
    assert submit.status_code == 200
    return purchase_order_id, po_line_item_id


def _receive_goods(client, purchase_order_id: str, po_line_item_id: str, suffix: str, qty_received: int) -> None:
    response = client.post(
        f"/purchase-orders/{purchase_order_id}/receive",
        headers={"X-Correlation-ID": f"it-pay-receive-{suffix}", "Idempotency-Key": f"it-pay-receive-{suffix}"},
        json={"received_by": "warehouse-agent", "line_items": [{"po_line_item_id": po_line_item_id, "qty_received": qty_received}]},
    )
    assert response.status_code == 200


def _create_invoice(client, purchase_order_id: str, suffix: str, invoice_amount: str) -> str:
    response = client.post(
        "/invoices",
        headers={"X-Correlation-ID": f"it-pay-invoice-create-{suffix}", "Idempotency-Key": f"it-pay-invoice-create-{suffix}"},
        json={
            "vendor_id": "V-100",
            "purchase_order_id": purchase_order_id,
            "invoice_number": f"INV-PAY-{suffix}",
            "invoice_amount": invoice_amount,
        },
    )
    assert response.status_code == 201
    return response.json()["invoice_id"]


def test_invoice_payment_integration_marks_invoice_paid_and_closes_purchase_order(client):
    purchase_order_id, po_line_item_id = _create_submitted_purchase_order(client, "close")
    _receive_goods(client, purchase_order_id, po_line_item_id, "close", 100)
    invoice_id = _create_invoice(client, purchase_order_id, "close", "1000.00")
    match = client.post(
        f"/invoices/{invoice_id}/match",
        headers={"X-Correlation-ID": "it-invoice-pay-match", "Idempotency-Key": "it-invoice-pay-match"},
    )
    assert match.status_code == 200
    approve = client.post(
        f"/invoices/{invoice_id}/approve",
        headers={"X-Correlation-ID": "it-invoice-pay-approve", "Idempotency-Key": "it-invoice-pay-approve"},
    )
    assert approve.status_code == 200

    response = client.post(
        f"/invoices/{invoice_id}/pay",
        headers={"X-Correlation-ID": "it-invoice-pay-1", "Idempotency-Key": "it-invoice-pay-1"},
    )

    assert response.status_code == 200
    session = get_session_factory()()
    try:
        invoice_row = session.get(InvoiceRow, invoice_id)
        purchase_order_row = session.get(PurchaseOrderRow, purchase_order_id)
        assert invoice_row is not None
        assert purchase_order_row is not None
        assert invoice_row.status == "PAID"
        assert invoice_row.paid_at is not None
        assert purchase_order_row.status == "CLOSED"
    finally:
        session.close()


def test_invoice_payment_integration_replay_does_not_change_terminal_state(client):
    purchase_order_id, po_line_item_id = _create_submitted_purchase_order(client, "replay")
    _receive_goods(client, purchase_order_id, po_line_item_id, "replay", 100)
    invoice_id = _create_invoice(client, purchase_order_id, "replay", "1000.00")
    match = client.post(
        f"/invoices/{invoice_id}/match",
        headers={"X-Correlation-ID": "it-invoice-pay-replay-match", "Idempotency-Key": "it-invoice-pay-replay-match"},
    )
    assert match.status_code == 200
    approve = client.post(
        f"/invoices/{invoice_id}/approve",
        headers={"X-Correlation-ID": "it-invoice-pay-replay-approve", "Idempotency-Key": "it-invoice-pay-replay-approve"},
    )
    assert approve.status_code == 200

    first = client.post(
        f"/invoices/{invoice_id}/pay",
        headers={"X-Correlation-ID": "it-invoice-pay-replay-1", "Idempotency-Key": "it-invoice-pay-replay"},
    )
    replay = client.post(
        f"/invoices/{invoice_id}/pay",
        headers={"X-Correlation-ID": "it-invoice-pay-replay-2", "Idempotency-Key": "it-invoice-pay-replay"},
    )

    assert first.status_code == 200
    assert replay.status_code == 200
    assert first.json() == replay.json()