from __future__ import annotations


def test_purchase_order_creation_integration_is_idempotent(client):
    payload = {
        "vendor_id": "V-100",
        "line_items": [
            {
                "sku": "SKU-1000",
                "description": "Cement Bags",
                "qty_ordered": 50,
                "unit_cost": "12.50",
            }
        ],
    }

    first = client.post(
        "/purchase-orders",
        headers={"X-Correlation-ID": "it-po-create-1", "Idempotency-Key": "it-po-create-1"},
        json=payload,
    )
    second = client.post(
        "/purchase-orders",
        headers={"X-Correlation-ID": "it-po-create-2", "Idempotency-Key": "it-po-create-1"},
        json=payload,
    )

    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["purchase_order_id"] == second.json()["purchase_order_id"]


def test_purchase_order_creation_integration_missing_vendor(client):
    response = client.post(
        "/purchase-orders",
        headers={"X-Correlation-ID": "it-po-create-missing", "Idempotency-Key": "it-po-create-missing"},
        json={
            "vendor_id": "V-999",
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

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "VENDOR_NOT_FOUND"


def test_purchase_order_creation_integration_rejects_conflicting_idempotency_replay(client):
    first = client.post(
        "/purchase-orders",
        headers={"X-Correlation-ID": "it-po-create-conflict-1", "Idempotency-Key": "it-po-create-conflict"},
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
    conflicting = client.post(
        "/purchase-orders",
        headers={"X-Correlation-ID": "it-po-create-conflict-2", "Idempotency-Key": "it-po-create-conflict"},
        json={
            "vendor_id": "V-100",
            "line_items": [
                {
                    "sku": "SKU-2000",
                    "description": "Rebar",
                    "qty_ordered": 10,
                    "unit_cost": "48.00",
                }
            ],
        },
    )

    assert first.status_code == 201
    assert conflicting.status_code == 409
    assert conflicting.json()["error"]["code"] == "IDEMPOTENCY_KEY_CONFLICT"