from __future__ import annotations


def _create_submit_receive_order(client) -> tuple[str, str]:
    create_response = client.post(
        "/purchase-orders",
        headers={"X-Correlation-ID": "contract-po-query-create", "Idempotency-Key": "contract-po-query-create"},
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

    submit_response = client.post(
        f"/purchase-orders/{purchase_order_id}/submit",
        headers={"X-Correlation-ID": "contract-po-query-submit", "Idempotency-Key": "contract-po-query-submit"},
    )
    assert submit_response.status_code == 200

    first_receipt = client.post(
        f"/purchase-orders/{purchase_order_id}/receive",
        headers={"X-Correlation-ID": "contract-po-query-receive-1", "Idempotency-Key": "contract-po-query-receive-1"},
        json={
            "received_by": "warehouse-agent",
            "line_items": [{"po_line_item_id": po_line_item_id, "qty_received": 20}],
        },
    )
    assert first_receipt.status_code == 200

    second_receipt = client.post(
        f"/purchase-orders/{purchase_order_id}/receive",
        headers={"X-Correlation-ID": "contract-po-query-receive-2", "Idempotency-Key": "contract-po-query-receive-2"},
        json={
            "received_by": "warehouse-agent",
            "line_items": [{"po_line_item_id": po_line_item_id, "qty_received": 30}],
        },
    )
    assert second_receipt.status_code == 200
    return purchase_order_id, po_line_item_id


def test_purchase_order_query_contract_zero_receipts(client):
    create_response = client.post(
        "/purchase-orders",
        headers={"X-Correlation-ID": "contract-po-query-zero-create", "Idempotency-Key": "contract-po-query-zero-create"},
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

    query_response = client.get(
        f"/purchase-orders/{purchase_order_id}",
        headers={"X-Correlation-ID": "contract-po-query-zero"},
    )

    assert query_response.status_code == 200
    body = query_response.json()
    assert body["status"] == "DRAFT"
    assert body["line_items"][0]["qty_received"] == 0
    assert body["line_items"][0]["qty_remaining"] == 50
    assert body["receipts"] == []


def test_purchase_order_query_contract_cumulative_progress(client):
    purchase_order_id, _ = _create_submit_receive_order(client)

    query_response = client.get(
        f"/purchase-orders/{purchase_order_id}",
        headers={"X-Correlation-ID": "contract-po-query-full"},
    )

    assert query_response.status_code == 200
    body = query_response.json()
    assert body["status"] == "RECEIVED"
    assert body["line_items"][0]["qty_received"] == 50
    assert body["line_items"][0]["qty_remaining"] == 0
    assert len(body["receipts"]) == 2
