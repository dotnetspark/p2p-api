from __future__ import annotations


def test_vendor_exposure_total_and_zero_case(client):
    exposure_response = client.get("/vendors/V-100/exposure", headers={"X-Correlation-ID": "it-us3-exposure"})
    zero_response = client.get("/vendors/V-200/exposure", headers={"X-Correlation-ID": "it-us3-zero"})

    assert exposure_response.status_code == 200
    assert exposure_response.json()["outstanding_total_amount"] == "1750.00"
    assert exposure_response.json()["open_invoice_count"] == 2

    assert zero_response.status_code == 200
    assert zero_response.json()["outstanding_total_amount"] == "0.00"
    assert zero_response.json()["open_invoice_count"] == 0