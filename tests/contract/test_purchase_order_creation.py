from __future__ import annotations


def test_purchase_order_creation_contract_active_vendor(client):
    response = client.post(
        "/purchase-orders",
        headers={
            "X-Correlation-ID": "contract-po-create-1",
            "Idempotency-Key": "contract-po-create-1",
        },
        json={
            "vendor_id": "V-100",
            "line_items": [
                {
                    "sku": "SKU-1000",
                    "description": "Cement Bags",
                    "qty_ordered": 50,
                    "unit_cost": "12.50",
                },
                {
                    "sku": "SKU-2000",
                    "description": "Rebar",
                    "qty_ordered": 10,
                    "unit_cost": "48.00",
                },
            ],
        },
    )

    assert response.status_code == 201
    assert response.headers["X-Correlation-ID"] == "contract-po-create-1"
    body = response.json()
    assert body["purchase_order_id"].startswith("PO-")
    assert body["vendor_id"] == "V-100"
    assert body["status"] == "DRAFT"
    assert body["receipts"] == []
    assert body["line_items"] == [
        {
            "po_line_item_id": body["line_items"][0]["po_line_item_id"],
            "sku": "SKU-1000",
            "description": "Cement Bags",
            "qty_ordered": 50,
            "qty_received": 0,
            "qty_remaining": 50,
        },
        {
            "po_line_item_id": body["line_items"][1]["po_line_item_id"],
            "sku": "SKU-2000",
            "description": "Rebar",
            "qty_ordered": 10,
            "qty_received": 0,
            "qty_remaining": 10,
        },
    ]


def test_purchase_order_creation_contract_inactive_vendor(client):
    response = client.post(
        "/purchase-orders",
        headers={
            "X-Correlation-ID": "contract-po-create-inactive",
            "Idempotency-Key": "contract-po-create-inactive",
        },
        json={
            "vendor_id": "V-300",
            "line_items": [
                {
                    "sku": "SKU-1000",
                    "description": "Cement Bags",
                    "qty_ordered": 10,
                    "unit_cost": "12.50",
                }
            ],
        },
    )

    assert response.status_code == 409
    body = response.json()
    assert body["error"]["code"] == "VENDOR_INACTIVE"
    assert body["error"]["retryable"] is False


def test_purchase_order_creation_contract_invalid_lines(client):
    response = client.post(
        "/purchase-orders",
        headers={
            "X-Correlation-ID": "contract-po-create-invalid",
            "Idempotency-Key": "contract-po-create-invalid",
        },
        json={
            "vendor_id": "V-100",
            "line_items": [
                {
                    "sku": "SKU-1000",
                    "description": "Cement Bags",
                    "qty_ordered": 0,
                    "unit_cost": "12.50",
                }
            ],
        },
    )

    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "PURCHASE_ORDER_LINE_INVALID"
    assert body["error"]["retryable"] is False


def test_purchase_order_creation_contract_rejects_idempotency_key_reuse_for_different_payload(client):
    first_response = client.post(
        "/purchase-orders",
        headers={
            "X-Correlation-ID": "contract-po-create-conflict-1",
            "Idempotency-Key": "contract-po-create-conflict",
        },
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
    assert first_response.status_code == 201

    conflicting_response = client.post(
        "/purchase-orders",
        headers={
            "X-Correlation-ID": "contract-po-create-conflict-2",
            "Idempotency-Key": "contract-po-create-conflict",
        },
        json={
            "vendor_id": "V-100",
            "line_items": [
                {
                    "sku": "SKU-9999",
                    "description": "Different Item",
                    "qty_ordered": 1,
                    "unit_cost": "99.99",
                }
            ],
        },
    )

    assert conflicting_response.status_code == 409
    body = conflicting_response.json()
    assert body["error"]["code"] == "IDEMPOTENCY_KEY_CONFLICT"
    assert body["error"]["retryable"] is False