from __future__ import annotations

from src.domain.services.vendor_credit_alert_service import VendorCreditAlertService
from src.persistence.database import get_session_factory
from src.persistence.models.credit_check import CreditCheckRow
from src.persistence.models.idempotency import IdempotencyKeyRow


def _create_submitted_purchase_order(client, suffix: str) -> tuple[str, str]:
    create = client.post(
        "/purchase-orders",
        headers={"X-Correlation-ID": f"it-credit-po-create-{suffix}", "Idempotency-Key": f"it-credit-po-create-{suffix}"},
        json={
            "vendor_id": "V-100",
            "line_items": [
                {
                    "sku": f"SKU-CREDIT-{suffix}",
                    "description": f"Credit Alert Item {suffix}",
                    "qty_ordered": 100,
                    "unit_cost": "10.00",
                }
            ],
        },
    )
    assert create.status_code == 201
    purchase_order_id = create.json()["purchase_order_id"]
    po_line_item_id = create.json()["line_items"][0]["po_line_item_id"]
    submit = client.post(
        f"/purchase-orders/{purchase_order_id}/submit",
        headers={"X-Correlation-ID": f"it-credit-po-submit-{suffix}", "Idempotency-Key": f"it-credit-po-submit-{suffix}"},
    )
    assert submit.status_code == 200
    return purchase_order_id, po_line_item_id


def _receive_goods(client, purchase_order_id: str, po_line_item_id: str, suffix: str, qty_received: int) -> None:
    response = client.post(
        f"/purchase-orders/{purchase_order_id}/receive",
        headers={"X-Correlation-ID": f"it-credit-receive-{suffix}", "Idempotency-Key": f"it-credit-receive-{suffix}"},
        json={"received_by": "warehouse-agent", "line_items": [{"po_line_item_id": po_line_item_id, "qty_received": qty_received}]},
    )
    assert response.status_code == 200


def _create_matched_invoice(client, suffix: str) -> str:
    purchase_order_id, po_line_item_id = _create_submitted_purchase_order(client, suffix)
    _receive_goods(client, purchase_order_id, po_line_item_id, suffix, 100)
    create = client.post(
        "/invoices",
        headers={"X-Correlation-ID": f"it-credit-invoice-create-{suffix}", "Idempotency-Key": f"it-credit-invoice-create-{suffix}"},
        json={
            "vendor_id": "V-100",
            "purchase_order_id": purchase_order_id,
            "invoice_number": f"INV-CREDIT-{suffix}",
            "invoice_amount": "1000.00",
        },
    )
    assert create.status_code == 201
    invoice_id = create.json()["invoice_id"]
    match = client.post(
        f"/invoices/{invoice_id}/match",
        headers={"X-Correlation-ID": f"it-credit-match-{suffix}", "Idempotency-Key": f"it-credit-match-{suffix}"},
    )
    assert match.status_code == 200
    return invoice_id


def test_invoice_create_integration_persists_pending_credit_check_and_reuses_it_on_replay(client, monkeypatch):
    monkeypatch.setattr(VendorCreditAlertService, "dispatch_pending_credit_check", lambda self, credit_check_id: None)
    purchase_order_id, _ = _create_submitted_purchase_order(client, "create")
    payload = {
        "vendor_id": "V-100",
        "purchase_order_id": purchase_order_id,
        "invoice_number": "INV-CREDIT-CREATE",
        "invoice_amount": "550.00",
    }

    first = client.post(
        "/invoices",
        headers={"X-Correlation-ID": "it-credit-create-1", "Idempotency-Key": "it-credit-create"},
        json=payload,
    )
    replay = client.post(
        "/invoices",
        headers={"X-Correlation-ID": "it-credit-create-2", "Idempotency-Key": "it-credit-create"},
        json=payload,
    )

    assert first.status_code == 201
    assert replay.status_code == 201
    first_body = first.json()
    replay_body = replay.json()
    assert first_body["credit_check_id"] == replay_body["credit_check_id"]

    session = get_session_factory()()
    try:
        credit_checks = session.query(CreditCheckRow).filter(CreditCheckRow.idempotency_key == "it-credit-create").all()
        assert len(credit_checks) == 1
        credit_check = credit_checks[0]
        assert credit_check.id == first_body["credit_check_id"]
        assert credit_check.vendor_id == "V-100"
        assert credit_check.triggering_invoice_id == first_body["invoice_id"]
        assert credit_check.triggering_action == "CREATE"
        assert credit_check.status == "PENDING"
        assert credit_check.correlation_id == "it-credit-create-1"
        assert credit_check.completed_at is None

        idempotency_record = session.get(IdempotencyKeyRow, "it-credit-create")
        assert idempotency_record is not None
        assert idempotency_record.resource_id == first_body["invoice_id"]
        assert idempotency_record.credit_check_id == first_body["credit_check_id"]
    finally:
        session.close()


def test_invoice_approve_integration_persists_pending_credit_check_and_reuses_it_on_replay(client, monkeypatch):
    monkeypatch.setattr(VendorCreditAlertService, "dispatch_pending_credit_check", lambda self, credit_check_id: None)
    invoice_id = _create_matched_invoice(client, "approve")

    first = client.post(
        f"/invoices/{invoice_id}/approve",
        headers={"X-Correlation-ID": "it-credit-approve-1", "Idempotency-Key": "it-credit-approve"},
    )
    replay = client.post(
        f"/invoices/{invoice_id}/approve",
        headers={"X-Correlation-ID": "it-credit-approve-2", "Idempotency-Key": "it-credit-approve"},
    )

    assert first.status_code == 200
    assert replay.status_code == 200
    first_body = first.json()
    replay_body = replay.json()
    assert first_body["credit_check_id"] == replay_body["credit_check_id"]

    session = get_session_factory()()
    try:
        credit_checks = session.query(CreditCheckRow).filter(CreditCheckRow.idempotency_key == "it-credit-approve").all()
        assert len(credit_checks) == 1
        credit_check = credit_checks[0]
        assert credit_check.id == first_body["credit_check_id"]
        assert credit_check.vendor_id == "V-100"
        assert credit_check.triggering_invoice_id == invoice_id
        assert credit_check.triggering_action == "APPROVE"
        assert credit_check.status == "PENDING"
        assert credit_check.correlation_id == "it-credit-approve-1"
        assert credit_check.completed_at is None

        idempotency_record = session.get(IdempotencyKeyRow, "it-credit-approve")
        assert idempotency_record is not None
        assert idempotency_record.resource_id == invoice_id
        assert idempotency_record.credit_check_id == first_body["credit_check_id"]
    finally:
        session.close()


def test_background_credit_check_completes_and_persists_single_active_alert(client):
    purchase_order_id, _ = _create_submitted_purchase_order(client, "breach-one")
    first = client.post(
        "/invoices",
        headers={"X-Correlation-ID": "it-credit-breach-1", "Idempotency-Key": "it-credit-breach-1"},
        json={
            "vendor_id": "V-100",
            "purchase_order_id": purchase_order_id,
            "invoice_number": "INV-CREDIT-BREACH-1",
            "invoice_amount": "550.00",
        },
    )
    assert first.status_code == 201

    second_purchase_order_id, _ = _create_submitted_purchase_order(client, "breach-two")
    second = client.post(
        "/invoices",
        headers={"X-Correlation-ID": "it-credit-breach-2", "Idempotency-Key": "it-credit-breach-2"},
        json={
            "vendor_id": "V-100",
            "purchase_order_id": second_purchase_order_id,
            "invoice_number": "INV-CREDIT-BREACH-2",
            "invoice_amount": "600.00",
        },
    )
    assert second.status_code == 201

    session = get_session_factory()()
    try:
        first_credit_check = session.get(CreditCheckRow, first.json()["credit_check_id"])
        second_credit_check = session.get(CreditCheckRow, second.json()["credit_check_id"])
        assert first_credit_check is not None
        assert second_credit_check is not None
        assert first_credit_check.status == "COMPLETED"
        assert first_credit_check.breached is True
        assert first_credit_check.alert_id is not None
        assert second_credit_check.status == "COMPLETED"
        assert second_credit_check.breached is True
        assert second_credit_check.alert_id is not None
        assert second_credit_check.alert_id != first_credit_check.alert_id
    finally:
        session.close()


def test_background_credit_check_clears_active_alert_after_later_non_breach(client):
    purchase_order_id, po_line_item_id = _create_submitted_purchase_order(client, "resolve-breach")
    _receive_goods(client, purchase_order_id, po_line_item_id, "resolve-breach", 100)
    create = client.post(
        "/invoices",
        headers={"X-Correlation-ID": "it-credit-resolve-create", "Idempotency-Key": "it-credit-resolve-create"},
        json={
            "vendor_id": "V-100",
            "purchase_order_id": purchase_order_id,
            "invoice_number": "INV-CREDIT-RESOLVE",
            "invoice_amount": "1000.00",
        },
    )
    assert create.status_code == 201
    invoice_id = create.json()["invoice_id"]

    match = client.post(
        f"/invoices/{invoice_id}/match",
        headers={"X-Correlation-ID": "it-credit-resolve-match", "Idempotency-Key": "it-credit-resolve-match"},
    )
    assert match.status_code == 200
    approve = client.post(
        f"/invoices/{invoice_id}/approve",
        headers={"X-Correlation-ID": "it-credit-resolve-approve", "Idempotency-Key": "it-credit-resolve-approve"},
    )
    assert approve.status_code == 200
    pay = client.post(
        f"/invoices/{invoice_id}/pay",
        headers={"X-Correlation-ID": "it-credit-resolve-pay", "Idempotency-Key": "it-credit-resolve-pay"},
    )
    assert pay.status_code == 200

    clear_purchase_order_id, _ = _create_submitted_purchase_order(client, "resolve-clear")
    clear = client.post(
        "/invoices",
        headers={"X-Correlation-ID": "it-credit-resolve-clear", "Idempotency-Key": "it-credit-resolve-clear"},
        json={
            "vendor_id": "V-100",
            "purchase_order_id": clear_purchase_order_id,
            "invoice_number": "INV-CREDIT-CLEAR",
            "invoice_amount": "100.00",
        },
    )
    assert clear.status_code == 201

    exposure = client.get("/vendors/V-100/exposure", headers={"X-Correlation-ID": "it-credit-resolve-exposure"})
    assert exposure.status_code == 200
    assert exposure.json().get("active_credit_alert") is None