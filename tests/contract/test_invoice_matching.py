from __future__ import annotations


def _create_submitted_purchase_order(client, suffix: str) -> tuple[str, str]:
    create = client.post(
        "/purchase-orders",
        headers={"X-Correlation-ID": f"contract-match-po-create-{suffix}", "Idempotency-Key": f"contract-match-po-create-{suffix}"},
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
    assert create.status_code == 201
    purchase_order_id = create.json()["purchase_order_id"]
    po_line_item_id = create.json()["line_items"][0]["po_line_item_id"]
    submit = client.post(
        f"/purchase-orders/{purchase_order_id}/submit",
        headers={"X-Correlation-ID": f"contract-match-po-submit-{suffix}", "Idempotency-Key": f"contract-match-po-submit-{suffix}"},
    )
    assert submit.status_code == 200
    return purchase_order_id, po_line_item_id


def _receive_goods(client, purchase_order_id: str, po_line_item_id: str, suffix: str, qty_received: int) -> None:
    response = client.post(
        f"/purchase-orders/{purchase_order_id}/receive",
        headers={"X-Correlation-ID": f"contract-match-receive-{suffix}", "Idempotency-Key": f"contract-match-receive-{suffix}"},
        json={"received_by": "warehouse-agent", "line_items": [{"po_line_item_id": po_line_item_id, "qty_received": qty_received}]},
    )
    assert response.status_code == 200


def _create_invoice(client, purchase_order_id: str, suffix: str, invoice_amount: str) -> str:
    response = client.post(
        "/invoices",
        headers={"X-Correlation-ID": f"contract-match-invoice-create-{suffix}", "Idempotency-Key": f"contract-match-invoice-create-{suffix}"},
        json={
            "vendor_id": "V-100",
            "purchase_order_id": purchase_order_id,
            "invoice_number": f"INV-MATCH-{suffix}",
            "invoice_amount": invoice_amount,
        },
    )
    assert response.status_code == 201
    return response.json()["invoice_id"]


def test_invoice_matching_contract_blocked_response(client):
    purchase_order_id, po_line_item_id = _create_submitted_purchase_order(client, "blocked")
    _receive_goods(client, purchase_order_id, po_line_item_id, "blocked", 60)
    invoice_id = _create_invoice(client, purchase_order_id, "blocked", "700.00")

    response = client.post(
        f"/invoices/{invoice_id}/match",
        headers={"X-Correlation-ID": "contract-invoice-match-blocked", "Idempotency-Key": "contract-invoice-match-blocked"},
    )

    assert response.status_code == 422
    assert response.headers["X-Correlation-ID"] == "contract-invoice-match-blocked"
    body = response.json()
    assert body["invoice_status"] == "PENDING"
    assert body["last_match_outcome"] == "BLOCKED"
    assert body["match_status"] == "BLOCKED"
    assert body["received_value"] == "600.00"
    assert body["ordered_value"] == "1000.00"
    assert body["difference_amount"] == "-100.00"
    assert body["shortfall_amount"] == "100.00"
    assert body["next_action"] == "WAIT_FOR_RECEIPT"
    assert body["all_lines_fully_received"] is False
    assert body["open_lines"] == [
        {
            "po_line_item_id": po_line_item_id,
            "sku": f"SKU-MATCH-blocked",
            "qty_remaining": 40,
            "remaining_value": "400.00",
        }
    ]


def test_invoice_matching_contract_conflicting_idempotency_reuse(client):
    first_purchase_order_id, first_po_line_item_id = _create_submitted_purchase_order(client, "conflict-a")
    second_purchase_order_id, second_po_line_item_id = _create_submitted_purchase_order(client, "conflict-b")
    _receive_goods(client, first_purchase_order_id, first_po_line_item_id, "conflict-a", 60)
    _receive_goods(client, second_purchase_order_id, second_po_line_item_id, "conflict-b", 60)
    first_invoice_id = _create_invoice(client, first_purchase_order_id, "conflict-a", "700.00")
    second_invoice_id = _create_invoice(client, second_purchase_order_id, "conflict-b", "700.00")

    first = client.post(
        f"/invoices/{first_invoice_id}/match",
        headers={"X-Correlation-ID": "contract-invoice-match-conflict-1", "Idempotency-Key": "contract-invoice-match-conflict"},
    )
    conflicting = client.post(
        f"/invoices/{second_invoice_id}/match",
        headers={"X-Correlation-ID": "contract-invoice-match-conflict-2", "Idempotency-Key": "contract-invoice-match-conflict"},
    )

    assert first.status_code == 422
    assert conflicting.status_code == 409
    assert conflicting.json()["error"]["code"] == "IDEMPOTENCY_KEY_CONFLICT"


def test_invoice_matching_contract_warning_and_clean_outcomes(client):
    warning_purchase_order_id, warning_po_line_item_id = _create_submitted_purchase_order(client, "warning")
    _receive_goods(client, warning_purchase_order_id, warning_po_line_item_id, "warning", 60)
    warning_invoice_id = _create_invoice(client, warning_purchase_order_id, "warning", "600.00")
    warning_response = client.post(
        f"/invoices/{warning_invoice_id}/match",
        headers={"X-Correlation-ID": "contract-invoice-match-warning", "Idempotency-Key": "contract-invoice-match-warning"},
    )

    clean_purchase_order_id, clean_po_line_item_id = _create_submitted_purchase_order(client, "clean")
    _receive_goods(client, clean_purchase_order_id, clean_po_line_item_id, "clean", 100)
    clean_invoice_id = _create_invoice(client, clean_purchase_order_id, "clean", "1000.00")
    clean_response = client.post(
        f"/invoices/{clean_invoice_id}/match",
        headers={"X-Correlation-ID": "contract-invoice-match-clean", "Idempotency-Key": "contract-invoice-match-clean"},
    )

    assert warning_response.status_code == 202
    warning_body = warning_response.json()
    assert warning_body["match_status"] == "MATCHED_WITH_WARNING"
    assert warning_body["last_match_outcome"] == "MATCHED_WITH_WARNING"
    assert warning_body["next_action"] == "PROCEED_TO_APPROVAL"
    assert warning_body["warning"]["code"] == "OPEN_RECEIPT_EXPOSURE"
    assert warning_body["warning"]["open_lines"] == [
        {
            "po_line_item_id": warning_po_line_item_id,
            "sku": f"SKU-MATCH-warning",
            "qty_remaining": 40,
            "remaining_value": "400.00",
        }
    ]

    assert clean_response.status_code == 200
    clean_body = clean_response.json()
    assert clean_body["match_status"] == "MATCHED"
    assert clean_body["all_lines_fully_received"] is True
    assert clean_body["open_lines"] == []
    assert clean_body["next_action"] == "PROCEED_TO_APPROVAL"
    assert "warning" not in clean_body
