from __future__ import annotations


def _create_draft_order(client, correlation_id: str, idempotency_key: str) -> str:
    response = client.post(
        "/purchase-orders",
        headers={"X-Correlation-ID": correlation_id, "Idempotency-Key": idempotency_key},
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


def test_purchase_order_submission_contract_success(client):
    purchase_order_id = _create_draft_order(client, "contract-po-submit-create", "contract-po-submit-create")

    response = client.post(
        f"/purchase-orders/{purchase_order_id}/submit",
        headers={
            "X-Correlation-ID": "contract-po-submit-1",
            "Idempotency-Key": "contract-po-submit-1",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["purchase_order_id"] == purchase_order_id
    assert body["status"] == "SUBMITTED"


def test_purchase_order_submission_contract_invalid_state(client):
    purchase_order_id = _create_draft_order(client, "contract-po-submit-create-2", "contract-po-submit-create-2")

    first_submit = client.post(
        f"/purchase-orders/{purchase_order_id}/submit",
        headers={
            "X-Correlation-ID": "contract-po-submit-2a",
            "Idempotency-Key": "contract-po-submit-2a",
        },
    )
    assert first_submit.status_code == 200

    second_submit = client.post(
        f"/purchase-orders/{purchase_order_id}/submit",
        headers={
            "X-Correlation-ID": "contract-po-submit-2b",
            "Idempotency-Key": "contract-po-submit-2b",
        },
    )

    assert second_submit.status_code == 409
    body = second_submit.json()
    assert body["error"]["code"] == "PURCHASE_ORDER_INVALID_STATE"
    assert body["error"]["retryable"] is False


def test_purchase_order_submission_contract_rejects_idempotency_key_reuse_for_different_order(client):
    first_purchase_order_id = _create_draft_order(
        client,
        "contract-po-submit-create-3a",
        "contract-po-submit-create-3a",
    )
    second_purchase_order_id = _create_draft_order(
        client,
        "contract-po-submit-create-3b",
        "contract-po-submit-create-3b",
    )

    first_submit = client.post(
        f"/purchase-orders/{first_purchase_order_id}/submit",
        headers={
            "X-Correlation-ID": "contract-po-submit-conflict-1",
            "Idempotency-Key": "contract-po-submit-conflict",
        },
    )
    assert first_submit.status_code == 200

    conflicting_submit = client.post(
        f"/purchase-orders/{second_purchase_order_id}/submit",
        headers={
            "X-Correlation-ID": "contract-po-submit-conflict-2",
            "Idempotency-Key": "contract-po-submit-conflict",
        },
    )

    assert conflicting_submit.status_code == 409
    body = conflicting_submit.json()
    assert body["error"]["code"] == "IDEMPOTENCY_KEY_CONFLICT"
    assert body["error"]["retryable"] is False