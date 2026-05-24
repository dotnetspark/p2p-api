from __future__ import annotations


def _create_submit_order(client, suffix: str) -> tuple[str, str]:
    create = client.post(
        "/purchase-orders",
        headers={"X-Correlation-ID": f"it-po-receive-create-{suffix}", "Idempotency-Key": f"it-po-receive-create-{suffix}"},
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
    purchase_order_id = create.json()["purchase_order_id"]
    po_line_item_id = create.json()["line_items"][0]["po_line_item_id"]
    submit = client.post(
        f"/purchase-orders/{purchase_order_id}/submit",
        headers={"X-Correlation-ID": f"it-po-receive-submit-{suffix}", "Idempotency-Key": f"it-po-receive-submit-{suffix}"},
    )
    assert submit.status_code == 200
    return purchase_order_id, po_line_item_id


def test_purchase_order_receiving_integration_accumulates_across_receipts(client):
    purchase_order_id, po_line_item_id = _create_submit_order(client, "1")

    first = client.post(
        f"/purchase-orders/{purchase_order_id}/receive",
        headers={"X-Correlation-ID": "it-po-receive-1", "Idempotency-Key": "it-po-receive-1"},
        json={"received_by": "warehouse-agent", "line_items": [{"po_line_item_id": po_line_item_id, "qty_received": 20}]},
    )
    second = client.post(
        f"/purchase-orders/{purchase_order_id}/receive",
        headers={"X-Correlation-ID": "it-po-receive-2", "Idempotency-Key": "it-po-receive-2"},
        json={"received_by": "warehouse-agent", "line_items": [{"po_line_item_id": po_line_item_id, "qty_received": 30}]},
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["line_items"][0]["qty_received"] == 20
    assert second.json()["line_items"][0]["qty_received"] == 50
    assert second.json()["status"] == "RECEIVED"


def test_purchase_order_receiving_integration_receipt_idempotency(client):
    purchase_order_id, po_line_item_id = _create_submit_order(client, "2")

    first = client.post(
        f"/purchase-orders/{purchase_order_id}/receive",
        headers={"X-Correlation-ID": "it-po-receive-idem-1", "Idempotency-Key": "it-po-receive-idem-1"},
        json={"received_by": "warehouse-agent", "line_items": [{"po_line_item_id": po_line_item_id, "qty_received": 20}]},
    )
    second = client.post(
        f"/purchase-orders/{purchase_order_id}/receive",
        headers={"X-Correlation-ID": "it-po-receive-idem-2", "Idempotency-Key": "it-po-receive-idem-1"},
        json={"received_by": "warehouse-agent", "line_items": [{"po_line_item_id": po_line_item_id, "qty_received": 20}]},
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["line_items"][0]["qty_received"] == second.json()["line_items"][0]["qty_received"] == 20
    assert len(second.json()["receipts"]) == 1


def test_purchase_order_receiving_integration_rejects_conflicting_idempotency_replay(client):
    first_purchase_order_id, first_po_line_item_id = _create_submit_order(client, "3a")
    second_purchase_order_id, second_po_line_item_id = _create_submit_order(client, "3b")

    first = client.post(
        f"/purchase-orders/{first_purchase_order_id}/receive",
        headers={"X-Correlation-ID": "it-po-receive-conflict-1", "Idempotency-Key": "it-po-receive-conflict"},
        json={"received_by": "warehouse-agent", "line_items": [{"po_line_item_id": first_po_line_item_id, "qty_received": 20}]},
    )
    conflicting = client.post(
        f"/purchase-orders/{second_purchase_order_id}/receive",
        headers={"X-Correlation-ID": "it-po-receive-conflict-2", "Idempotency-Key": "it-po-receive-conflict"},
        json={"received_by": "warehouse-agent", "line_items": [{"po_line_item_id": second_po_line_item_id, "qty_received": 20}]},
    )

    assert first.status_code == 200
    assert conflicting.status_code == 409
    assert conflicting.json()["error"]["code"] == "IDEMPOTENCY_KEY_CONFLICT"