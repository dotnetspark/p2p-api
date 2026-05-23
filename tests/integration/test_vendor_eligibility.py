from __future__ import annotations


def test_vendor_eligibility_active_and_inactive(client):
    active_response = client.get("/vendors/V-100/eligibility", headers={"X-Correlation-ID": "it-us1-active"})
    inactive_response = client.get("/vendors/V-300/eligibility", headers={"X-Correlation-ID": "it-us1-inactive"})

    assert active_response.status_code == 200
    assert active_response.json()["obligations_allowed"] is True

    assert inactive_response.status_code == 200
    assert inactive_response.json()["obligations_allowed"] is False
    assert inactive_response.json()["blocking_reason_code"] == "VENDOR_INACTIVE"
