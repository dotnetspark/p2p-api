from __future__ import annotations


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
