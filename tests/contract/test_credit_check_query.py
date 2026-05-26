from __future__ import annotations

from src.domain.services.vendor_credit_alert_service import VendorCreditAlertService


def _create_submitted_purchase_order(client, suffix: str, vendor_id: str) -> str:
    create = client.post(
        "/purchase-orders",
        headers={"X-Correlation-ID": f"contract-credit-query-po-create-{suffix}", "Idempotency-Key": f"contract-credit-query-po-create-{suffix}"},
        json={
            "vendor_id": vendor_id,
            "line_items": [
                {
                    "sku": f"SKU-CREDIT-QUERY-{suffix}",
                    "description": f"Credit Check Query Item {suffix}",
                    "qty_ordered": 100,
                    "unit_cost": "10.00",
                }
            ],
        },
    )
    assert create.status_code == 201
    purchase_order_id = create.json()["purchase_order_id"]
    submit = client.post(
        f"/purchase-orders/{purchase_order_id}/submit",
        headers={"X-Correlation-ID": f"contract-credit-query-po-submit-{suffix}", "Idempotency-Key": f"contract-credit-query-po-submit-{suffix}"},
    )
    assert submit.status_code == 200
    return purchase_order_id


def test_credit_check_query_contract_pending(client, monkeypatch):
    monkeypatch.setattr(VendorCreditAlertService, "dispatch_pending_credit_check", lambda self, credit_check_id: None)
    purchase_order_id = _create_submitted_purchase_order(client, "pending", "V-200")
    create = client.post(
        "/invoices",
        headers={"X-Correlation-ID": "contract-credit-query-create-pending", "Idempotency-Key": "contract-credit-query-create-pending"},
        json={
            "vendor_id": "V-200",
            "purchase_order_id": purchase_order_id,
            "invoice_number": "INV-CREDIT-QUERY-PENDING",
            "invoice_amount": "250.00",
        },
    )
    assert create.status_code == 201

    response = client.get(
        f"/credit-checks/{create.json()['credit_check_id']}",
        headers={"X-Correlation-ID": "contract-credit-query-pending"},
    )

    assert response.status_code == 200
    assert response.headers["X-Correlation-ID"] == "contract-credit-query-pending"
    assert response.json() == {"status": "PENDING", "breached": None, "alert_id": None}


def test_credit_check_query_contract_completed_without_breach(client):
    purchase_order_id = _create_submitted_purchase_order(client, "clear", "V-200")
    create = client.post(
        "/invoices",
        headers={"X-Correlation-ID": "contract-credit-query-create-clear", "Idempotency-Key": "contract-credit-query-create-clear"},
        json={
            "vendor_id": "V-200",
            "purchase_order_id": purchase_order_id,
            "invoice_number": "INV-CREDIT-QUERY-CLEAR",
            "invoice_amount": "250.00",
        },
    )
    assert create.status_code == 201

    response = client.get(
        f"/credit-checks/{create.json()['credit_check_id']}",
        headers={"X-Correlation-ID": "contract-credit-query-clear"},
    )

    assert response.status_code == 200
    assert response.json() == {"status": "COMPLETED", "breached": False, "alert_id": None}


def test_credit_check_query_contract_completed_with_breach(client):
    purchase_order_id = _create_submitted_purchase_order(client, "breach", "V-100")
    create = client.post(
        "/invoices",
        headers={"X-Correlation-ID": "contract-credit-query-create-breach", "Idempotency-Key": "contract-credit-query-create-breach"},
        json={
            "vendor_id": "V-100",
            "purchase_order_id": purchase_order_id,
            "invoice_number": "INV-CREDIT-QUERY-BREACH",
            "invoice_amount": "550.00",
        },
    )
    assert create.status_code == 201

    response = client.get(
        f"/credit-checks/{create.json()['credit_check_id']}",
        headers={"X-Correlation-ID": "contract-credit-query-breach"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "COMPLETED"
    assert body["breached"] is True
    assert body["alert_id"].startswith("ALERT-")


def test_credit_check_query_contract_missing_credit_check(client):
    response = client.get("/credit-checks/CHK-404", headers={"X-Correlation-ID": "contract-credit-query-missing"})

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "CREDIT_CHECK_NOT_FOUND"