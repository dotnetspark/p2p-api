from __future__ import annotations


def _create_submitted_purchase_order(client, suffix: str) -> tuple[str, str]:
    create = client.post(
        "/purchase-orders",
        headers={"X-Correlation-ID": f"contract-pay-po-create-{suffix}", "Idempotency-Key": f"contract-pay-po-create-{suffix}"},
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
        headers={"X-Correlation-ID": f"contract-pay-po-submit-{suffix}", "Idempotency-Key": f"contract-pay-po-submit-{suffix}"},
    )
    assert submit.status_code == 200
    return purchase_order_id, po_line_item_id


def _receive_goods(client, purchase_order_id: str, po_line_item_id: str, suffix: str, qty_received: int) -> None:
    response = client.post(
        f"/purchase-orders/{purchase_order_id}/receive",
        headers={"X-Correlation-ID": f"contract-pay-receive-{suffix}", "Idempotency-Key": f"contract-pay-receive-{suffix}"},
        json={"received_by": "warehouse-agent", "line_items": [{"po_line_item_id": po_line_item_id, "qty_received": qty_received}]},
    )
    assert response.status_code == 200


def _create_invoice(client, purchase_order_id: str, suffix: str, invoice_amount: str) -> str:
    response = client.post(
        "/invoices",
        headers={"X-Correlation-ID": f"contract-pay-invoice-create-{suffix}", "Idempotency-Key": f"contract-pay-invoice-create-{suffix}"},
        json={
            "vendor_id": "V-100",
            "purchase_order_id": purchase_order_id,
            "invoice_number": f"INV-PAY-{suffix}",
            "invoice_amount": invoice_amount,
        },
    )
    assert response.status_code == 201
    return response.json()["invoice_id"]


def _create_approved_invoice(client, suffix: str) -> str:
    purchase_order_id, po_line_item_id = _create_submitted_purchase_order(client, suffix)
    _receive_goods(client, purchase_order_id, po_line_item_id, suffix, 100)
    invoice_id = _create_invoice(client, purchase_order_id, suffix, "1000.00")
    match = client.post(
        f"/invoices/{invoice_id}/match",
        headers={"X-Correlation-ID": f"contract-pay-match-{suffix}", "Idempotency-Key": f"contract-pay-match-{suffix}"},
    )
    assert match.status_code == 200
    approve = client.post(
        f"/invoices/{invoice_id}/approve",
        headers={"X-Correlation-ID": f"contract-pay-approve-{suffix}", "Idempotency-Key": f"contract-pay-approve-{suffix}"},
    )
    assert approve.status_code == 200
    return invoice_id


def test_invoice_payment_contract_success_and_replay(client):
    invoice_id = _create_approved_invoice(client, "success")

    first = client.post(
        f"/invoices/{invoice_id}/pay",
        headers={"X-Correlation-ID": "contract-invoice-pay-1", "Idempotency-Key": "contract-invoice-pay-1"},
    )
    replay = client.post(
        f"/invoices/{invoice_id}/pay",
        headers={"X-Correlation-ID": "contract-invoice-pay-2", "Idempotency-Key": "contract-invoice-pay-1"},
    )

    assert first.status_code == 200
    assert replay.status_code == 200
    assert first.headers["X-Correlation-ID"] == "contract-invoice-pay-1"
    body = first.json()
    replay_body = replay.json()
    assert body["invoice_id"] == invoice_id
    assert body["invoice_status"] == "PAID"
    assert body["purchase_order_status"] == "CLOSED"
    assert body["next_action"] == "COMPLETE"
    assert body == replay_body


def test_invoice_payment_contract_rejects_invalid_invoice_state(client):
    purchase_order_id, _ = _create_submitted_purchase_order(client, "invalid-state")
    invoice_id = _create_invoice(client, purchase_order_id, "invalid-state", "1000.00")

    response = client.post(
        f"/invoices/{invoice_id}/pay",
        headers={"X-Correlation-ID": "contract-invoice-pay-invalid-state", "Idempotency-Key": "contract-invoice-pay-invalid-state"},
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "INVOICE_INVALID_STATE"


def test_invoice_payment_contract_conflicting_idempotency_reuse(client):
    first_invoice_id = _create_approved_invoice(client, "conflict-a")
    second_invoice_id = _create_approved_invoice(client, "conflict-b")

    first = client.post(
        f"/invoices/{first_invoice_id}/pay",
        headers={"X-Correlation-ID": "contract-invoice-pay-conflict-1", "Idempotency-Key": "contract-invoice-pay-conflict"},
    )
    conflicting = client.post(
        f"/invoices/{second_invoice_id}/pay",
        headers={"X-Correlation-ID": "contract-invoice-pay-conflict-2", "Idempotency-Key": "contract-invoice-pay-conflict"},
    )

    assert first.status_code == 200
    assert conflicting.status_code == 409
    assert conflicting.json()["error"]["code"] == "IDEMPOTENCY_KEY_CONFLICT"