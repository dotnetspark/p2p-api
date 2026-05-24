from __future__ import annotations


def _create_and_submit_order(client, suffix: str) -> tuple[str, str]:
    create_response = client.post(
        "/purchase-orders",
        headers={"X-Correlation-ID": f"contract-po-receive-create-{suffix}", "Idempotency-Key": f"contract-po-receive-create-{suffix}"},
        json={
            "vendor_id": "V-100",
            "line_items": [
                {
                    "sku": "SKU-1000",
                    "description": "Cement Bags",
                    "qty_ordered": 50,
                    "unit_cost": "12.50",
                }
            ],
        },
    )
    assert create_response.status_code == 201
    purchase_order_id = create_response.json()["purchase_order_id"]
    po_line_item_id = create_response.json()["line_items"][0]["po_line_item_id"]

    submit_response = client.post(
        f"/purchase-orders/{purchase_order_id}/submit",
        headers={"X-Correlation-ID": f"contract-po-receive-submit-{suffix}", "Idempotency-Key": f"contract-po-receive-submit-{suffix}"},
    )
    assert submit_response.status_code == 200
    return purchase_order_id, po_line_item_id


def test_purchase_order_receiving_contract_additive_success(client):
    purchase_order_id, po_line_item_id = _create_and_submit_order(client, "1")

    response = client.post(
        f"/purchase-orders/{purchase_order_id}/receive",
        headers={"X-Correlation-ID": "contract-po-receive-1", "Idempotency-Key": "contract-po-receive-1"},
        json={
            "received_by": "warehouse-agent",
            "line_items": [{"po_line_item_id": po_line_item_id, "qty_received": 20}],
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "SUBMITTED"
    assert body["line_items"][0]["qty_received"] == 20
    assert body["line_items"][0]["qty_remaining"] == 30
    assert len(body["receipts"]) == 1


def test_purchase_order_receiving_contract_overreceipt_rejected(client):
    purchase_order_id, po_line_item_id = _create_and_submit_order(client, "2")

    accepted = client.post(
        f"/purchase-orders/{purchase_order_id}/receive",
        headers={"X-Correlation-ID": "contract-po-receive-2a", "Idempotency-Key": "contract-po-receive-2a"},
        json={
            "received_by": "warehouse-agent",
            "line_items": [{"po_line_item_id": po_line_item_id, "qty_received": 40}],
        },
    )
    assert accepted.status_code == 200

    rejected = client.post(
        f"/purchase-orders/{purchase_order_id}/receive",
        headers={"X-Correlation-ID": "contract-po-receive-2b", "Idempotency-Key": "contract-po-receive-2b"},
        json={
            "received_by": "warehouse-agent",
            "line_items": [{"po_line_item_id": po_line_item_id, "qty_received": 20}],
        },
    )

    assert rejected.status_code == 409
    body = rejected.json()
    assert body["error"]["code"] == "PURCHASE_ORDER_OVER_RECEIPT"
    assert body["error"]["retryable"] is False


def test_purchase_order_receiving_contract_requires_submitted_order(client):
    create_response = client.post(
        "/purchase-orders",
        headers={"X-Correlation-ID": "contract-po-receive-draft-create", "Idempotency-Key": "contract-po-receive-draft-create"},
        json={
            "vendor_id": "V-100",
            "line_items": [
                {
                    "sku": "SKU-1000",
                    "description": "Cement Bags",
                    "qty_ordered": 50,
                    "unit_cost": "12.50",
                }
            ],
        },
    )
    purchase_order_id = create_response.json()["purchase_order_id"]
    po_line_item_id = create_response.json()["line_items"][0]["po_line_item_id"]

    response = client.post(
        f"/purchase-orders/{purchase_order_id}/receive",
        headers={"X-Correlation-ID": "contract-po-receive-draft", "Idempotency-Key": "contract-po-receive-draft"},
        json={
            "received_by": "warehouse-agent",
            "line_items": [{"po_line_item_id": po_line_item_id, "qty_received": 20}],
        },
    )

    assert response.status_code == 409
    body = response.json()
    assert body["error"]["code"] == "PURCHASE_ORDER_INVALID_STATE"


def test_purchase_order_receiving_contract_rejects_idempotency_key_reuse_for_different_order(client):
    first_purchase_order_id, first_po_line_item_id = _create_and_submit_order(client, "3a")
    second_purchase_order_id, second_po_line_item_id = _create_and_submit_order(client, "3b")

    first_receipt = client.post(
        f"/purchase-orders/{first_purchase_order_id}/receive",
        headers={
            "X-Correlation-ID": "contract-po-receive-conflict-1",
            "Idempotency-Key": "contract-po-receive-conflict",
        },
        json={
            "received_by": "warehouse-agent",
            "line_items": [{"po_line_item_id": first_po_line_item_id, "qty_received": 10}],
        },
    )
    assert first_receipt.status_code == 200

    conflicting_receipt = client.post(
        f"/purchase-orders/{second_purchase_order_id}/receive",
        headers={
            "X-Correlation-ID": "contract-po-receive-conflict-2",
            "Idempotency-Key": "contract-po-receive-conflict",
        },
        json={
            "received_by": "warehouse-agent",
            "line_items": [{"po_line_item_id": second_po_line_item_id, "qty_received": 10}],
        },
    )

    assert conflicting_receipt.status_code == 409
    body = conflicting_receipt.json()
    assert body["error"]["code"] == "IDEMPOTENCY_KEY_CONFLICT"
    assert body["error"]["retryable"] is False