from __future__ import annotations


def _create_submitted_purchase_order(client, suffix: str, vendor_id: str = "V-100") -> tuple[str, str]:
    create = client.post(
        "/purchase-orders",
        headers={"X-Correlation-ID": f"it-vendor-exposure-po-create-{suffix}", "Idempotency-Key": f"it-vendor-exposure-po-create-{suffix}"},
        json={
            "vendor_id": vendor_id,
            "line_items": [
                {
                    "sku": f"SKU-IT-VENDOR-EXPOSURE-{suffix}",
                    "description": f"Vendor Exposure Item {suffix}",
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
        headers={"X-Correlation-ID": f"it-vendor-exposure-po-submit-{suffix}", "Idempotency-Key": f"it-vendor-exposure-po-submit-{suffix}"},
    )
    assert submit.status_code == 200
    return purchase_order_id, po_line_item_id


def _receive_match_approve_pay(client, purchase_order_id: str, po_line_item_id: str, invoice_id: str, suffix: str) -> None:
    receive = client.post(
        f"/purchase-orders/{purchase_order_id}/receive",
        headers={"X-Correlation-ID": f"it-vendor-exposure-receive-{suffix}", "Idempotency-Key": f"it-vendor-exposure-receive-{suffix}"},
        json={"received_by": "warehouse-agent", "line_items": [{"po_line_item_id": po_line_item_id, "qty_received": 100}]},
    )
    assert receive.status_code == 200
    match = client.post(
        f"/invoices/{invoice_id}/match",
        headers={"X-Correlation-ID": f"it-vendor-exposure-match-{suffix}", "Idempotency-Key": f"it-vendor-exposure-match-{suffix}"},
    )
    assert match.status_code == 200
    approve = client.post(
        f"/invoices/{invoice_id}/approve",
        headers={"X-Correlation-ID": f"it-vendor-exposure-approve-{suffix}", "Idempotency-Key": f"it-vendor-exposure-approve-{suffix}"},
    )
    assert approve.status_code == 200
    pay = client.post(
        f"/invoices/{invoice_id}/pay",
        headers={"X-Correlation-ID": f"it-vendor-exposure-pay-{suffix}", "Idempotency-Key": f"it-vendor-exposure-pay-{suffix}"},
    )
    assert pay.status_code == 200


def test_vendor_exposure_total_and_zero_case(client):
    exposure_response = client.get("/vendors/V-100/exposure", headers={"X-Correlation-ID": "it-us3-exposure"})
    zero_response = client.get("/vendors/V-200/exposure", headers={"X-Correlation-ID": "it-us3-zero"})

    assert exposure_response.status_code == 200
    assert exposure_response.json()["outstanding_total_amount"] == "1750.00"
    assert exposure_response.json()["open_invoice_count"] == 2

    assert zero_response.status_code == 200
    assert zero_response.json()["outstanding_total_amount"] == "0.00"
    assert zero_response.json()["open_invoice_count"] == 0


def test_vendor_exposure_integration_includes_active_credit_alert_after_breach(client):
    purchase_order_id, _ = _create_submitted_purchase_order(client, "breach")
    create = client.post(
        "/invoices",
        headers={"X-Correlation-ID": "it-vendor-exposure-create-breach", "Idempotency-Key": "it-vendor-exposure-create-breach"},
        json={
            "vendor_id": "V-100",
            "purchase_order_id": purchase_order_id,
            "invoice_number": "INV-IT-VENDOR-EXPOSURE-BREACH",
            "invoice_amount": "550.00",
        },
    )
    assert create.status_code == 201

    exposure = client.get("/vendors/V-100/exposure", headers={"X-Correlation-ID": "it-vendor-exposure-breach"})

    assert exposure.status_code == 200
    body = exposure.json()
    assert body["active_credit_alert"]["credit_check_id"] == create.json()["credit_check_id"]
    assert body["active_credit_alert"]["outstanding_amount"] == "2300.00"
    assert body["active_credit_alert"]["credit_limit"] == "2000.00"
    assert body["active_credit_alert"]["percentage_consumed"] == "115.00"


def test_vendor_exposure_integration_omits_active_credit_alert_after_resolution(client):
    purchase_order_id, po_line_item_id = _create_submitted_purchase_order(client, "resolve-breach")
    create = client.post(
        "/invoices",
        headers={"X-Correlation-ID": "it-vendor-exposure-create-resolve", "Idempotency-Key": "it-vendor-exposure-create-resolve"},
        json={
            "vendor_id": "V-100",
            "purchase_order_id": purchase_order_id,
            "invoice_number": "INV-IT-VENDOR-EXPOSURE-RESOLVE",
            "invoice_amount": "1000.00",
        },
    )
    assert create.status_code == 201
    _receive_match_approve_pay(client, purchase_order_id, po_line_item_id, create.json()["invoice_id"], "resolve-breach")

    clear_purchase_order_id, _ = _create_submitted_purchase_order(client, "resolve-clear")
    clear = client.post(
        "/invoices",
        headers={"X-Correlation-ID": "it-vendor-exposure-create-clear", "Idempotency-Key": "it-vendor-exposure-create-clear"},
        json={
            "vendor_id": "V-100",
            "purchase_order_id": clear_purchase_order_id,
            "invoice_number": "INV-IT-VENDOR-EXPOSURE-CLEAR",
            "invoice_amount": "100.00",
        },
    )
    assert clear.status_code == 201

    exposure = client.get("/vendors/V-100/exposure", headers={"X-Correlation-ID": "it-vendor-exposure-clear"})

    assert exposure.status_code == 200
    assert exposure.json().get("active_credit_alert") is None