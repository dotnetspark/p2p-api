from __future__ import annotations

from src.domain.services.vendor_credit_alert_service import VendorCreditAlertService
from src.persistence.database import get_session_factory
from src.persistence.models.credit_alert import CreditAlertRow
from src.persistence.models.credit_check import CreditCheckRow


def _create_submitted_purchase_order(client, suffix: str, vendor_id: str) -> str:
    create = client.post(
        "/purchase-orders",
        headers={"X-Correlation-ID": f"it-credit-query-po-create-{suffix}", "Idempotency-Key": f"it-credit-query-po-create-{suffix}"},
        json={
            "vendor_id": vendor_id,
            "line_items": [
                {
                    "sku": f"SKU-IT-CREDIT-QUERY-{suffix}",
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
        headers={"X-Correlation-ID": f"it-credit-query-po-submit-{suffix}", "Idempotency-Key": f"it-credit-query-po-submit-{suffix}"},
    )
    assert submit.status_code == 200
    return purchase_order_id


def test_credit_check_query_integration_returns_pending_when_background_dispatch_is_stubbed(client, monkeypatch):
    monkeypatch.setattr(VendorCreditAlertService, "dispatch_pending_credit_check", lambda self, credit_check_id: None)
    purchase_order_id = _create_submitted_purchase_order(client, "pending", "V-200")
    create = client.post(
        "/invoices",
        headers={"X-Correlation-ID": "it-credit-query-create-pending", "Idempotency-Key": "it-credit-query-create-pending"},
        json={
            "vendor_id": "V-200",
            "purchase_order_id": purchase_order_id,
            "invoice_number": "INV-IT-CREDIT-QUERY-PENDING",
            "invoice_amount": "250.00",
        },
    )
    assert create.status_code == 201

    response = client.get(
        f"/credit-checks/{create.json()['credit_check_id']}",
        headers={"X-Correlation-ID": "it-credit-query-pending"},
    )

    assert response.status_code == 200
    assert response.json() == {"status": "PENDING", "breached": None, "alert_id": None}


def test_credit_check_query_integration_returns_completed_breach_with_alert_correlation(client):
    purchase_order_id = _create_submitted_purchase_order(client, "breach", "V-100")
    create = client.post(
        "/invoices",
        headers={"X-Correlation-ID": "it-credit-query-create-breach", "Idempotency-Key": "it-credit-query-create-breach"},
        json={
            "vendor_id": "V-100",
            "purchase_order_id": purchase_order_id,
            "invoice_number": "INV-IT-CREDIT-QUERY-BREACH",
            "invoice_amount": "550.00",
        },
    )
    assert create.status_code == 201
    credit_check_id = create.json()["credit_check_id"]

    response = client.get(
        f"/credit-checks/{credit_check_id}",
        headers={"X-Correlation-ID": "it-credit-query-breach"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "COMPLETED"
    assert body["breached"] is True

    session = get_session_factory()()
    try:
        credit_check = session.get(CreditCheckRow, credit_check_id)
        alert = session.get(CreditAlertRow, body["alert_id"])
        assert credit_check is not None
        assert credit_check.status == "COMPLETED"
        assert credit_check.alert_id == body["alert_id"]
        assert alert is not None
        assert alert.credit_check_id == credit_check_id
        assert alert.vendor_id == "V-100"
    finally:
        session.close()