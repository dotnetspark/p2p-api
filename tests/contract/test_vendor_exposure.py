from __future__ import annotations


def _create_submitted_purchase_order(client, suffix: str, vendor_id: str = "V-100") -> tuple[str, str]:
    create = client.post(
        "/purchase-orders",
        headers={"X-Correlation-ID": f"contract-vendor-exposure-po-create-{suffix}", "Idempotency-Key": f"contract-vendor-exposure-po-create-{suffix}"},
        json={
            "vendor_id": vendor_id,
            "line_items": [
                {
                    "sku": f"SKU-VENDOR-EXPOSURE-{suffix}",
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
        headers={"X-Correlation-ID": f"contract-vendor-exposure-po-submit-{suffix}", "Idempotency-Key": f"contract-vendor-exposure-po-submit-{suffix}"},
    )
    assert submit.status_code == 200
    return purchase_order_id, po_line_item_id


def _receive_match_approve_pay(client, purchase_order_id: str, po_line_item_id: str, invoice_id: str, suffix: str) -> None:
    receive = client.post(
        f"/purchase-orders/{purchase_order_id}/receive",
        headers={"X-Correlation-ID": f"contract-vendor-exposure-receive-{suffix}", "Idempotency-Key": f"contract-vendor-exposure-receive-{suffix}"},
        json={"received_by": "warehouse-agent", "line_items": [{"po_line_item_id": po_line_item_id, "qty_received": 100}]},
    )
    assert receive.status_code == 200
    match = client.post(
        f"/invoices/{invoice_id}/match",
        headers={"X-Correlation-ID": f"contract-vendor-exposure-match-{suffix}", "Idempotency-Key": f"contract-vendor-exposure-match-{suffix}"},
    )
    assert match.status_code == 200
    approve = client.post(
        f"/invoices/{invoice_id}/approve",
        headers={"X-Correlation-ID": f"contract-vendor-exposure-approve-{suffix}", "Idempotency-Key": f"contract-vendor-exposure-approve-{suffix}"},
    )
    assert approve.status_code == 200
    pay = client.post(
        f"/invoices/{invoice_id}/pay",
        headers={"X-Correlation-ID": f"contract-vendor-exposure-pay-{suffix}", "Idempotency-Key": f"contract-vendor-exposure-pay-{suffix}"},
    )
    assert pay.status_code == 200


def test_vendor_exposure_contract(client):
    response = client.get("/vendors/V-100/exposure", headers={"X-Correlation-ID": "contract-us3-exposure"})

    assert response.status_code == 200
    assert response.headers["X-Correlation-ID"] == "contract-us3-exposure"
    body = response.json()
    assert body["vendor_id"] == "V-100"
    assert body["vendor_name"] == "ACME Building Supply"
    assert body["outstanding_total_amount"] == "1750.00"
    assert body["open_invoice_count"] == 2
    assert body["included_invoice_statuses"] == ["PENDING", "MATCHED", "APPROVED"]


def test_vendor_exposure_missing_vendor_contract(client):
    response = client.get("/vendors/V-999/exposure", headers={"X-Correlation-ID": "contract-us3-missing"})

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "VENDOR_NOT_FOUND"


def test_vendor_exposure_contract_includes_active_credit_alert_after_breach(client):
    purchase_order_id, _ = _create_submitted_purchase_order(client, "breach")
    create = client.post(
        "/invoices",
        headers={"X-Correlation-ID": "contract-vendor-exposure-create-breach", "Idempotency-Key": "contract-vendor-exposure-create-breach"},
        json={
            "vendor_id": "V-100",
            "purchase_order_id": purchase_order_id,
            "invoice_number": "INV-VENDOR-EXPOSURE-BREACH",
            "invoice_amount": "550.00",
        },
    )
    assert create.status_code == 201

    response = client.get("/vendors/V-100/exposure", headers={"X-Correlation-ID": "contract-vendor-exposure-breach"})

    assert response.status_code == 200
    alert = response.json()["active_credit_alert"]
    assert alert["alert_id"].startswith("ALERT-")
    assert alert["vendor_id"] == "V-100"
    assert alert["credit_check_id"] == create.json()["credit_check_id"]
    assert alert["triggering_invoice_id"] == create.json()["invoice_id"]
    assert alert["credit_limit"] == "2000.00"


def test_vendor_exposure_contract_omits_active_credit_alert_after_resolution(client):
    purchase_order_id, po_line_item_id = _create_submitted_purchase_order(client, "resolve-breach")
    create = client.post(
        "/invoices",
        headers={"X-Correlation-ID": "contract-vendor-exposure-create-resolve", "Idempotency-Key": "contract-vendor-exposure-create-resolve"},
        json={
            "vendor_id": "V-100",
            "purchase_order_id": purchase_order_id,
            "invoice_number": "INV-VENDOR-EXPOSURE-RESOLVE",
            "invoice_amount": "1000.00",
        },
    )
    assert create.status_code == 201
    _receive_match_approve_pay(client, purchase_order_id, po_line_item_id, create.json()["invoice_id"], "resolve-breach")

    clear_purchase_order_id, _ = _create_submitted_purchase_order(client, "resolve-clear")
    clear = client.post(
        "/invoices",
        headers={"X-Correlation-ID": "contract-vendor-exposure-create-clear", "Idempotency-Key": "contract-vendor-exposure-create-clear"},
        json={
            "vendor_id": "V-100",
            "purchase_order_id": clear_purchase_order_id,
            "invoice_number": "INV-VENDOR-EXPOSURE-CLEAR",
            "invoice_amount": "100.00",
        },
    )
    assert clear.status_code == 201

    response = client.get("/vendors/V-100/exposure", headers={"X-Correlation-ID": "contract-vendor-exposure-clear"})

    assert response.status_code == 200
    assert response.json().get("active_credit_alert") is None
