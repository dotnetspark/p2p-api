from __future__ import annotations


def _create_order(client, suffix: str) -> str:
    response = client.post(
        "/purchase-orders",
        headers={"X-Correlation-ID": f"it-po-submit-create-{suffix}", "Idempotency-Key": f"it-po-submit-create-{suffix}"},
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
    assert response.status_code == 201
    return response.json()["purchase_order_id"]


def test_purchase_order_submission_integration_is_idempotent(client):
    purchase_order_id = _create_order(client, "1")

    first = client.post(
        f"/purchase-orders/{purchase_order_id}/submit",
        headers={"X-Correlation-ID": "it-po-submit-1", "Idempotency-Key": "it-po-submit-1"},
    )
    second = client.post(
        f"/purchase-orders/{purchase_order_id}/submit",
        headers={"X-Correlation-ID": "it-po-submit-2", "Idempotency-Key": "it-po-submit-1"},
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["status"] == second.json()["status"] == "SUBMITTED"


def test_purchase_order_submission_integration_rejects_conflicting_idempotency_replay(client):
    first_purchase_order_id = _create_order(client, "2a")
    second_purchase_order_id = _create_order(client, "2b")

    first = client.post(
        f"/purchase-orders/{first_purchase_order_id}/submit",
        headers={"X-Correlation-ID": "it-po-submit-conflict-1", "Idempotency-Key": "it-po-submit-conflict"},
    )
    conflicting = client.post(
        f"/purchase-orders/{second_purchase_order_id}/submit",
        headers={"X-Correlation-ID": "it-po-submit-conflict-2", "Idempotency-Key": "it-po-submit-conflict"},
    )

    assert first.status_code == 200
    assert conflicting.status_code == 409
    assert conflicting.json()["error"]["code"] == "IDEMPOTENCY_KEY_CONFLICT"
