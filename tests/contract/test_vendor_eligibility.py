from __future__ import annotations


def test_vendor_eligibility_contract_active_vendor(client):
    response = client.get("/vendors/V-100/eligibility", headers={"X-Correlation-ID": "contract-us1-active"})

    assert response.status_code == 200
    assert response.headers["X-Correlation-ID"] == "contract-us1-active"
    body = response.json()
    assert body == {
        "vendor_id": "V-100",
        "vendor_name": "ACME Building Supply",
        "is_active": True,
        "obligations_allowed": True,
        "blocking_reason_code": None,
        "blocking_reason_message": None,
    }


def test_vendor_eligibility_contract_missing_vendor(client):
    response = client.get("/vendors/V-999/eligibility", headers={"X-Correlation-ID": "contract-us1-missing"})

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "VENDOR_NOT_FOUND"
    assert response.json()["error"]["retryable"] is False
