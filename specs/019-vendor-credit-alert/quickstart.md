# Quickstart: Vendor Credit Alert

## Purpose

Validate that invoice creation and approval now schedule a decoupled vendor credit
check, return a deterministic top-level `credit_check_id`, expose check state
through `GET /credit-checks/{id}`, and surface any active alert through the existing
vendor exposure endpoint.

## Prerequisites

- Python 3.14 installed
- Project dependencies installed into the repo virtual environment
- Seed data with at least one vendor that has a configured credit limit
- At least one invoice workflow that can create or approve an invoice for that vendor

## Run The API

```powershell
c:/Users/ylrre/source/repos/p2p-api/.venv/Scripts/python.exe -m pip install -e .[dev]
c:/Users/ylrre/source/repos/p2p-api/.venv/Scripts/python.exe -m uvicorn src.main:app --reload
```

## Create An Invoice And Capture The Credit Check Identifier

```powershell
curl -i -X POST http://localhost:8000/invoices \
  -H "X-Correlation-ID: credit-alert-create-1" \
  -H "Idempotency-Key: credit-alert-create-1" \
  -H "Content-Type: application/json" \
  -d '{
    "vendor_id": "V-100",
    "purchase_order_id": "PO-ALERT-100",
    "invoice_number": "INV-ALERT-100",
    "invoice_amount": "3500.00"
  }'
```

Expected result:

- HTTP `201`
- Existing invoice-create fields are unchanged
- Response adds a top-level `credit_check_id`, for example:

```json
{
  "invoice_id": "INV-ALERT-100",
  "vendor_id": "V-100",
  "purchase_order_id": "PO-ALERT-100",
  "invoice_number": "INV-ALERT-100",
  "invoice_amount": "3500.00",
  "status": "PENDING",
  "last_match_outcome": "NONE",
  "next_action": "REQUEST_MATCH",
  "credit_check_id": "CHK-123"
}
```

- The background task runs after the response is sent
- Any exception inside that task is logged silently and does not alter the `201`

## Query The Credit Check While It Is Still Pending

```powershell
curl -i http://localhost:8000/credit-checks/CHK-123 \
  -H "X-Correlation-ID: credit-alert-check-1"
```

Expected result before the task completes:

- HTTP `200`
- Response body:

```json
{
  "status": "PENDING",
  "breached": null,
  "alert_id": null
}
```

## Query The Credit Check After Completion

```powershell
curl -i http://localhost:8000/credit-checks/CHK-123 \
  -H "X-Correlation-ID: credit-alert-check-2"
```

Expected result when no breach is found:

```json
{
  "status": "COMPLETED",
  "breached": false,
  "alert_id": null
}
```

Expected result when the vendor exceeds the limit:

```json
{
  "status": "COMPLETED",
  "breached": true,
  "alert_id": "ALERT-456"
}
```

## Approve A Matched Invoice And Reuse The Same Pattern

```powershell
curl -i -X POST http://localhost:8000/invoices/INV-ALERT-100/approve \
  -H "X-Correlation-ID: credit-alert-approve-1" \
  -H "Idempotency-Key: credit-alert-approve-1"
```

Expected result:

- HTTP `200`
- Existing invoice-approval fields are unchanged
- Response adds a top-level `credit_check_id` with the newly created or replayed identifier

## Retrieve Vendor Exposure At The Next Checkpoint

```powershell
curl -i http://localhost:8000/vendors/V-100/exposure \
  -H "X-Correlation-ID: credit-alert-exposure-1"
```

Expected result when vendor exposure exceeds the credit limit:

- HTTP `200`
- Existing exposure summary fields are present
- `active_credit_alert` is present with `alert_id`, `vendor_id`, `credit_check_id`, `triggering_invoice_id`, `outstanding_amount`, `credit_limit`, `percentage_consumed`, `breached_at`, and `advisory_only`

Expected result when exposure does not exceed the credit limit:

- HTTP `200`
- Existing exposure summary fields are present
- `active_credit_alert` is omitted entirely

## Replay Safety Check

```powershell
curl -i -X POST http://localhost:8000/invoices/INV-ALERT-100/approve \
  -H "X-Correlation-ID: credit-alert-approve-replay" \
  -H "Idempotency-Key: credit-alert-approve-1"
```

Expected result:

- The approval response replays the original logical outcome
- The replay returns the same top-level `credit_check_id`
- The replay does not dispatch a duplicate background credit check
- A later non-breached credit check clears any stale active vendor alert for that vendor

## Validation Notes

- The breach rule is `outstanding_total_amount > credit_limit`
- Outstanding AP is computed from invoices in `PENDING`, `MATCHED`, or `APPROVED`
- The feature retains only the most recent active alert per vendor
- No new router module is introduced; the public credit-check query path is implemented in the invoices routing surface
