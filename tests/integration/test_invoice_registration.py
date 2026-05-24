from __future__ import annotations


def _create_submitted_purchase_order(client, suffix: str, vendor_id: str = "V-100") -> str:
    create = client.post(
        "/purchase-orders",
        headers={"X-Correlation-ID": f"it-invoice-po-create-{suffix}", "Idempotency-Key": f"it-invoice-po-create-{suffix}"},
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
    purchase_order_id = create.json()["purchase_order_id"]
    submit = client.post(
        f"/purchase-orders/{purchase_order_id}/submit",
        headers={"X-Correlation-ID": f"it-invoice-po-submit-{suffix}", "Idempotency-Key": f"it-invoice-po-submit-{suffix}"},
    )
    assert create.status_code == 201
    assert submit.status_code == 200
    return purchase_order_id


def test_invoice_registration_integration_pending_state(client):
    purchase_order_id = _create_submitted_purchase_order(client, "pending")

    response = client.post(
        "/invoices",
        headers={"X-Correlation-ID": "it-invoice-create-pending", "Idempotency-Key": "it-invoice-create-pending"},
        json={
            "vendor_id": "V-100",
            "purchase_order_id": purchase_order_id,
            "invoice_number": "INV-PENDING-100",
            "invoice_amount": "350.00",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "PENDING"
    assert body["last_match_outcome"] == "NONE"
    assert body["next_action"] == "REQUEST_MATCH"


def test_invoice_registration_integration_vendor_purchase_order_mismatch(client):
    purchase_order_id = _create_submitted_purchase_order(client, "mismatch", vendor_id="V-100")

    response = client.post(
        "/invoices",
        headers={"X-Correlation-ID": "it-invoice-mismatch", "Idempotency-Key": "it-invoice-mismatch"},
        json={
            "vendor_id": "V-200",
            "purchase_order_id": purchase_order_id,
            "invoice_number": "INV-MISMATCH-100",
            "invoice_amount": "350.00",
        },
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "INVOICE_VENDOR_PO_MISMATCH"


def test_invoice_registration_integration_duplicate_reference(client):
    first_purchase_order_id = _create_submitted_purchase_order(client, "dup-a")
    second_purchase_order_id = _create_submitted_purchase_order(client, "dup-b")

    first = client.post(
        "/invoices",
        headers={"X-Correlation-ID": "it-invoice-dup-1", "Idempotency-Key": "it-invoice-dup-1"},
        json={
            "vendor_id": "V-100",
            "purchase_order_id": first_purchase_order_id,
            "invoice_number": "INV-DUP-200",
            "invoice_amount": "500.00",
        },
    )
    duplicate = client.post(
        "/invoices",
        headers={"X-Correlation-ID": "it-invoice-dup-2", "Idempotency-Key": "it-invoice-dup-2"},
        json={
            "vendor_id": "V-100",
            "purchase_order_id": second_purchase_order_id,
            "invoice_number": "INV-DUP-200",
            "invoice_amount": "500.00",
        },
    )

    assert first.status_code == 201
    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "INVOICE_DUPLICATE_REFERENCE"


def test_invoice_registration_integration_rejects_non_positive_amount(client):
    purchase_order_id = _create_submitted_purchase_order(client, "invalid-amount")

    response = client.post(
        "/invoices",
        headers={"X-Correlation-ID": "it-invoice-invalid-amount", "Idempotency-Key": "it-invoice-invalid-amount"},
        json={
            "vendor_id": "V-100",
            "purchase_order_id": purchase_order_id,
            "invoice_number": "INV-INVALID-AMOUNT-200",
            "invoice_amount": "0.00",
        },
    )

    assert response.status_code == 422


def test_invoice_registration_integration_rejects_second_invoice_for_purchase_order(client):
    purchase_order_id = _create_submitted_purchase_order(client, "single-po")

    first = client.post(
        "/invoices",
        headers={"X-Correlation-ID": "it-invoice-single-po-1", "Idempotency-Key": "it-invoice-single-po-1"},
        json={
            "vendor_id": "V-100",
            "purchase_order_id": purchase_order_id,
            "invoice_number": "INV-SINGLE-PO-200",
            "invoice_amount": "500.00",
        },
    )
    second = client.post(
        "/invoices",
        headers={"X-Correlation-ID": "it-invoice-single-po-2", "Idempotency-Key": "it-invoice-single-po-2"},
        json={
            "vendor_id": "V-100",
            "purchase_order_id": purchase_order_id,
            "invoice_number": "INV-SINGLE-PO-201",
            "invoice_amount": "400.00",
        },
    )

    assert first.status_code == 201
    assert second.status_code == 409
    assert second.json()["error"]["code"] == "PURCHASE_ORDER_INVALID_STATE"
