from __future__ import annotations


def _create_submitted_purchase_order(client, suffix: str) -> tuple[str, str]:
    create = client.post(
        "/purchase-orders",
        headers={"X-Correlation-ID": f"it-match-po-create-{suffix}", "Idempotency-Key": f"it-match-po-create-{suffix}"},
        json={
            "vendor_id": "V-100",
            "line_items": [
                {
                    "sku": f"SKU-MATCH-{suffix}",
                    "description": f"Match Item {suffix}",
                    "qty_ordered": 100,
                    "unit_cost": "10.00",
                }
            ],
        },
    )
    purchase_order_id = create.json()["purchase_order_id"]
    po_line_item_id = create.json()["line_items"][0]["po_line_item_id"]
    submit = client.post(
        f"/purchase-orders/{purchase_order_id}/submit",
        headers={"X-Correlation-ID": f"it-match-po-submit-{suffix}", "Idempotency-Key": f"it-match-po-submit-{suffix}"},
    )
    assert create.status_code == 201
    assert submit.status_code == 200
    return purchase_order_id, po_line_item_id


def _receive_goods(client, purchase_order_id: str, po_line_item_id: str, suffix: str, qty_received: int) -> None:
    response = client.post(
        f"/purchase-orders/{purchase_order_id}/receive",
        headers={"X-Correlation-ID": f"it-match-receive-{suffix}", "Idempotency-Key": f"it-match-receive-{suffix}"},
        json={"received_by": "warehouse-agent", "line_items": [{"po_line_item_id": po_line_item_id, "qty_received": qty_received}]},
    )
    assert response.status_code == 200


def _create_invoice(client, purchase_order_id: str, suffix: str, invoice_amount: str) -> str:
    response = client.post(
        "/invoices",
        headers={"X-Correlation-ID": f"it-match-invoice-create-{suffix}", "Idempotency-Key": f"it-match-invoice-create-{suffix}"},
        json={
            "vendor_id": "V-100",
            "purchase_order_id": purchase_order_id,
            "invoice_number": f"INV-MATCH-{suffix}",
            "invoice_amount": invoice_amount,
        },
    )
    assert response.status_code == 201
    return response.json()["invoice_id"]


def test_invoice_matching_integration_wait_for_receipt(client):
    purchase_order_id, po_line_item_id = _create_submitted_purchase_order(client, "wait")
    _receive_goods(client, purchase_order_id, po_line_item_id, "wait", 60)
    invoice_id = _create_invoice(client, purchase_order_id, "wait", "700.00")

    response = client.post(
        f"/invoices/{invoice_id}/match",
        headers={"X-Correlation-ID": "it-invoice-match-wait", "Idempotency-Key": "it-invoice-match-wait"},
    )

    assert response.status_code == 422
    body = response.json()
    assert body["next_action"] == "WAIT_FOR_RECEIPT"
    assert body["shortfall_amount"] == "100.00"
    assert body["difference_amount"] == "-100.00"


def test_invoice_matching_integration_correct_invoice(client):
    purchase_order_id, po_line_item_id = _create_submitted_purchase_order(client, "correct")
    _receive_goods(client, purchase_order_id, po_line_item_id, "correct", 60)
    invoice_id = _create_invoice(client, purchase_order_id, "correct", "1100.00")

    response = client.post(
        f"/invoices/{invoice_id}/match",
        headers={"X-Correlation-ID": "it-invoice-match-correct", "Idempotency-Key": "it-invoice-match-correct"},
    )

    assert response.status_code == 422
    assert response.json()["next_action"] == "CORRECT_INVOICE"


def test_invoice_matching_integration_exact_equality_warning(client):
    purchase_order_id, po_line_item_id = _create_submitted_purchase_order(client, "equality")
    _receive_goods(client, purchase_order_id, po_line_item_id, "equality", 60)
    invoice_id = _create_invoice(client, purchase_order_id, "equality", "600.00")

    response = client.post(
        f"/invoices/{invoice_id}/match",
        headers={"X-Correlation-ID": "it-invoice-match-equality", "Idempotency-Key": "it-invoice-match-equality"},
    )

    assert response.status_code == 202
    body = response.json()
    assert body["match_status"] == "MATCHED_WITH_WARNING"
    assert body["difference_amount"] == "0.00"
    assert body["all_lines_fully_received"] is False
    assert body["warning"]["code"] == "OPEN_RECEIPT_EXPOSURE"


def test_invoice_matching_integration_rematch_after_additional_receipts(client):
    purchase_order_id, po_line_item_id = _create_submitted_purchase_order(client, "rematch")
    _receive_goods(client, purchase_order_id, po_line_item_id, "rematch-a", 60)
    invoice_id = _create_invoice(client, purchase_order_id, "rematch", "600.00")

    first = client.post(
        f"/invoices/{invoice_id}/match",
        headers={"X-Correlation-ID": "it-invoice-match-rematch-1", "Idempotency-Key": "it-invoice-match-rematch-1"},
    )
    _receive_goods(client, purchase_order_id, po_line_item_id, "rematch-b", 40)
    replay = client.post(
        f"/invoices/{invoice_id}/match",
        headers={"X-Correlation-ID": "it-invoice-match-rematch-2", "Idempotency-Key": "it-invoice-match-rematch-1"},
    )
    refreshed = client.post(
        f"/invoices/{invoice_id}/match",
        headers={"X-Correlation-ID": "it-invoice-match-rematch-3", "Idempotency-Key": "it-invoice-match-rematch-2"},
    )

    assert first.status_code == 202
    assert replay.status_code == 202
    assert replay.json()["match_status"] == "MATCHED_WITH_WARNING"
    assert refreshed.status_code == 200
    assert refreshed.json()["match_status"] == "MATCHED"
    assert refreshed.json()["open_lines"] == []
