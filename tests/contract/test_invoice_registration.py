from __future__ import annotations


def _create_submitted_purchase_order(client, suffix: str, vendor_id: str = "V-100") -> str:
    create = client.post(
        "/purchase-orders",
        headers={"X-Correlation-ID": f"contract-invoice-po-create-{suffix}", "Idempotency-Key": f"contract-invoice-po-create-{suffix}"},
        json={
            "vendor_id": vendor_id,
            "line_items": [
                {
                    "sku": f"SKU-{suffix}",
                    "description": f"Invoice Registration Item {suffix}",
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
        headers={"X-Correlation-ID": f"contract-invoice-po-submit-{suffix}", "Idempotency-Key": f"contract-invoice-po-submit-{suffix}"},
    )
    assert submit.status_code == 200
    return purchase_order_id


def test_invoice_registration_contract_success(client):
    purchase_order_id = _create_submitted_purchase_order(client, "success")

    response = client.post(
        "/invoices",
        headers={"X-Correlation-ID": "contract-invoice-create-1", "Idempotency-Key": "contract-invoice-create-1"},
        json={
            "vendor_id": "V-100",
            "purchase_order_id": purchase_order_id,
            "invoice_number": "INV-REG-100",
            "invoice_amount": "550.00",
        },
    )

    assert response.status_code == 201
    assert response.headers["X-Correlation-ID"] == "contract-invoice-create-1"
    body = response.json()
    assert body["invoice_id"].startswith("INV-")
    assert body["vendor_id"] == "V-100"
    assert body["purchase_order_id"] == purchase_order_id
    assert body["invoice_number"] == "INV-REG-100"
    assert body["invoice_amount"] == "550.00"
    assert body["status"] == "PENDING"
    assert body["last_match_outcome"] == "NONE"
    assert body["next_action"] == "REQUEST_MATCH"
    assert body["credit_check_id"].startswith("CHK-")


def test_invoice_registration_contract_duplicate_reference(client):
    first_purchase_order_id = _create_submitted_purchase_order(client, "dup-1")
    second_purchase_order_id = _create_submitted_purchase_order(client, "dup-2")

    first = client.post(
        "/invoices",
        headers={"X-Correlation-ID": "contract-invoice-dup-1", "Idempotency-Key": "contract-invoice-dup-1"},
        json={
            "vendor_id": "V-100",
            "purchase_order_id": first_purchase_order_id,
            "invoice_number": "INV-DUP-100",
            "invoice_amount": "500.00",
        },
    )
    duplicate = client.post(
        "/invoices",
        headers={"X-Correlation-ID": "contract-invoice-dup-2", "Idempotency-Key": "contract-invoice-dup-2"},
        json={
            "vendor_id": "V-100",
            "purchase_order_id": second_purchase_order_id,
            "invoice_number": "INV-DUP-100",
            "invoice_amount": "500.00",
        },
    )

    assert first.status_code == 201
    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "INVOICE_DUPLICATE_REFERENCE"


def test_invoice_registration_contract_rejects_non_positive_amount(client):
    purchase_order_id = _create_submitted_purchase_order(client, "invalid-amount")

    response = client.post(
        "/invoices",
        headers={"X-Correlation-ID": "contract-invoice-invalid-amount", "Idempotency-Key": "contract-invoice-invalid-amount"},
        json={
            "vendor_id": "V-100",
            "purchase_order_id": purchase_order_id,
            "invoice_number": "INV-INVALID-AMOUNT-100",
            "invoice_amount": "0.00",
        },
    )

    assert response.status_code == 422


def test_invoice_registration_contract_rejects_second_invoice_for_purchase_order(client):
    purchase_order_id = _create_submitted_purchase_order(client, "single-po")

    first = client.post(
        "/invoices",
        headers={"X-Correlation-ID": "contract-invoice-single-po-1", "Idempotency-Key": "contract-invoice-single-po-1"},
        json={
            "vendor_id": "V-100",
            "purchase_order_id": purchase_order_id,
            "invoice_number": "INV-SINGLE-PO-100",
            "invoice_amount": "500.00",
        },
    )
    second = client.post(
        "/invoices",
        headers={"X-Correlation-ID": "contract-invoice-single-po-2", "Idempotency-Key": "contract-invoice-single-po-2"},
        json={
            "vendor_id": "V-100",
            "purchase_order_id": purchase_order_id,
            "invoice_number": "INV-SINGLE-PO-101",
            "invoice_amount": "400.00",
        },
    )

    assert first.status_code == 201
    assert second.status_code == 409
    assert second.json()["error"]["code"] == "PURCHASE_ORDER_INVALID_STATE"


def test_invoice_registration_contract_idempotent_replay(client):
    purchase_order_id = _create_submitted_purchase_order(client, "idem")
    payload = {
        "vendor_id": "V-100",
        "purchase_order_id": purchase_order_id,
        "invoice_number": "INV-IDEM-100",
        "invoice_amount": "425.00",
    }

    first = client.post(
        "/invoices",
        headers={"X-Correlation-ID": "contract-invoice-idem-1", "Idempotency-Key": "contract-invoice-idem-1"},
        json=payload,
    )
    replay = client.post(
        "/invoices",
        headers={"X-Correlation-ID": "contract-invoice-idem-2", "Idempotency-Key": "contract-invoice-idem-1"},
        json=payload,
    )

    assert first.status_code == 201
    assert replay.status_code == 201
    assert first.json()["invoice_id"] == replay.json()["invoice_id"]
    assert first.json()["credit_check_id"] == replay.json()["credit_check_id"]
