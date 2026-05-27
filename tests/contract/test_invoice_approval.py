from __future__ import annotations


def _create_submitted_purchase_order(client, suffix: str) -> tuple[str, str]:
    create = client.post(
        "/purchase-orders",
        headers={"X-Correlation-ID": f"contract-approve-po-create-{suffix}", "Idempotency-Key": f"contract-approve-po-create-{suffix}"},
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
        headers={"X-Correlation-ID": f"contract-approve-po-submit-{suffix}", "Idempotency-Key": f"contract-approve-po-submit-{suffix}"},
    )
    assert submit.status_code == 200
    return purchase_order_id, po_line_item_id


def _receive_goods(client, purchase_order_id: str, po_line_item_id: str, suffix: str, qty_received: int) -> None:
    response = client.post(
        f"/purchase-orders/{purchase_order_id}/receive",
        headers={"X-Correlation-ID": f"contract-approve-receive-{suffix}", "Idempotency-Key": f"contract-approve-receive-{suffix}"},
        json={"received_by": "warehouse-agent", "line_items": [{"po_line_item_id": po_line_item_id, "qty_received": qty_received}]},
    )
    assert response.status_code == 200


def _create_invoice(client, purchase_order_id: str, suffix: str, invoice_amount: str) -> str:
    response = client.post(
        "/invoices",
        headers={"X-Correlation-ID": f"contract-approve-invoice-create-{suffix}", "Idempotency-Key": f"contract-approve-invoice-create-{suffix}"},
        json={
            "vendor_id": "V-100",
            "purchase_order_id": purchase_order_id,
            "invoice_number": f"INV-APPROVE-{suffix}",
            "invoice_amount": invoice_amount,
        },
    )
    assert response.status_code == 201
    return response.json()["invoice_id"]


def _create_matched_invoice(client, suffix: str) -> str:
    purchase_order_id, po_line_item_id = _create_submitted_purchase_order(client, suffix)
    _receive_goods(client, purchase_order_id, po_line_item_id, suffix, 100)
    invoice_id = _create_invoice(client, purchase_order_id, suffix, "1000.00")
    match = client.post(
        f"/invoices/{invoice_id}/match",
        headers={"X-Correlation-ID": f"contract-approve-match-{suffix}", "Idempotency-Key": f"contract-approve-match-{suffix}"},
    )
    assert match.status_code == 200
    return invoice_id


def test_invoice_approval_contract_success_and_replay(client):
    invoice_id = _create_matched_invoice(client, "success")

    first = client.post(
        f"/invoices/{invoice_id}/approve",
        headers={"X-Correlation-ID": "contract-invoice-approve-1", "Idempotency-Key": "contract-invoice-approve-1"},
    )
    replay = client.post(
        f"/invoices/{invoice_id}/approve",
        headers={"X-Correlation-ID": "contract-invoice-approve-2", "Idempotency-Key": "contract-invoice-approve-1"},
    )

    assert first.status_code == 200
    assert replay.status_code == 200
    assert first.headers["X-Correlation-ID"] == "contract-invoice-approve-1"
    body = first.json()
    replay_body = replay.json()
    assert body["invoice_id"] == invoice_id
    assert body["invoice_status"] == "APPROVED"
    assert body["purchase_order_id"].startswith("PO-")
    assert len(body["generated_gl_entries"]) == 2
    assert body["generated_gl_entries"] == replay_body["generated_gl_entries"]
    assert body["next_action"] == "MARK_PAID"
    assert body["credit_check_id"].startswith("CHK-")
    assert body["credit_check_id"] == replay_body["credit_check_id"]
    assert {entry["account_code"] for entry in body["generated_gl_entries"]} == {"AP_CONTROL", "EXPENSE_BUILDING_SUPPLY"}
    ap_control_entry = next(entry for entry in body["generated_gl_entries"] if entry["account_code"] == "AP_CONTROL")
    expense_entry = next(entry for entry in body["generated_gl_entries"] if entry["account_code"] == "EXPENSE_BUILDING_SUPPLY")
    assert ap_control_entry["debit"] == "0.00"
    assert ap_control_entry["credit"] == "1000.00"
    assert expense_entry["debit"] == "1000.00"
    assert expense_entry["credit"] == "0.00"


def test_invoice_approval_contract_rejects_invalid_invoice_state(client):
    purchase_order_id, _ = _create_submitted_purchase_order(client, "invalid-state")
    invoice_id = _create_invoice(client, purchase_order_id, "invalid-state", "1000.00")

    response = client.post(
        f"/invoices/{invoice_id}/approve",
        headers={"X-Correlation-ID": "contract-invoice-approve-invalid-state", "Idempotency-Key": "contract-invoice-approve-invalid-state"},
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "INVOICE_INVALID_STATE"


def test_invoice_approval_contract_conflicting_idempotency_reuse(client):
    first_invoice_id = _create_matched_invoice(client, "conflict-a")
    second_invoice_id = _create_matched_invoice(client, "conflict-b")

    first = client.post(
        f"/invoices/{first_invoice_id}/approve",
        headers={"X-Correlation-ID": "contract-invoice-approve-conflict-1", "Idempotency-Key": "contract-invoice-approve-conflict"},
    )
    conflicting = client.post(
        f"/invoices/{second_invoice_id}/approve",
        headers={"X-Correlation-ID": "contract-invoice-approve-conflict-2", "Idempotency-Key": "contract-invoice-approve-conflict"},
    )

    assert first.status_code == 200
    assert conflicting.status_code == 409
    assert conflicting.json()["error"]["code"] == "IDEMPOTENCY_KEY_CONFLICT"