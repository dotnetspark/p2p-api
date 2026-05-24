from __future__ import annotations


def test_purchase_order_query_integration_supports_invoicing_readiness_decision(client):
    create = client.post(
        "/purchase-orders",
        headers={"X-Correlation-ID": "it-po-query-create", "Idempotency-Key": "it-po-query-create"},
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
    client.post(
        f"/purchase-orders/{purchase_order_id}/submit",
        headers={"X-Correlation-ID": "it-po-query-submit", "Idempotency-Key": "it-po-query-submit"},
    )
    client.post(
        f"/purchase-orders/{purchase_order_id}/receive",
        headers={"X-Correlation-ID": "it-po-query-receive", "Idempotency-Key": "it-po-query-receive"},
        json={"received_by": "warehouse-agent", "line_items": [{"po_line_item_id": po_line_item_id, "qty_received": 20}]},
    )

    query = client.get(
        f"/purchase-orders/{purchase_order_id}",
        headers={"X-Correlation-ID": "it-po-query"},
    )

    assert query.status_code == 200
    body = query.json()
    assert body["status"] == "SUBMITTED"
    assert body["line_items"][0]["qty_received"] == 20
    assert body["line_items"][0]["qty_remaining"] == 30
    assert len(body["receipts"]) == 1