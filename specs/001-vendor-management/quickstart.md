# Quickstart: Vendor Management

## Purpose

Validate the vendor eligibility and AP exposure contracts for the PoC API using the
planned Python 3.14, FastAPI, SQLAlchemy 2.x, and SQLite stack.

## Prerequisites

- Python 3.14 installed
- Project dependencies installed via editable project install
- Seed data containing at least one active vendor, one inactive vendor, and invoices in
  both unpaid and paid states

## Seed Data Assumptions

- `V-100` is active and has two unpaid invoices totaling `1750.00`
- `V-200` is active and has zero unpaid invoices
- `V-300` is inactive and is rejected by the shared inactive-vendor guard

## Run the API

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .[dev]
uvicorn src.main:app --reload
```

## Validate Vendor Eligibility

### Active vendor

```powershell
curl -s -H "X-Correlation-ID: test-eligibility-active" http://localhost:8000/vendors/V-100/eligibility
```

Expected result:

- HTTP 200
- `obligations_allowed = true`
- `blocking_reason_code = null`

### Inactive vendor

```powershell
curl -s -H "X-Correlation-ID: test-eligibility-inactive" http://localhost:8000/vendors/V-300/eligibility
```

Expected result:

- HTTP 200
- `is_active = false`
- `obligations_allowed = false`
- stable blocking reason code identifying the inactive vendor condition

## Validate Vendor Exposure

```powershell
curl -s -H "X-Correlation-ID: test-exposure" http://localhost:8000/vendors/V-100/exposure
```

Expected result:

- HTTP 200
- `outstanding_total_amount` equals the sum of all unpaid invoices for the vendor
- `open_invoice_count` matches the number of unpaid invoices used in the calculation
- `included_invoice_statuses` shows which statuses contributed to the result

## Validate Zero Exposure Behavior

```powershell
curl -s -H "X-Correlation-ID: test-zero-exposure" http://localhost:8000/vendors/V-200/exposure
```

Expected result:

- HTTP 200
- `outstanding_total_amount = 0`
- `open_invoice_count = 0`
- no retry or business error is returned

## Validate Error Semantics

### Missing vendor

```powershell
curl -i -H "X-Correlation-ID: test-missing-vendor" http://localhost:8000/vendors/V-999/eligibility
```

Expected result:

- HTTP 404
- stable error code `VENDOR_NOT_FOUND`
- correlation ID echoed in the response

### Temporary infrastructure failure

Simulate an unavailable SQLite store or forced repository failure.

Expected result:

- retryable 5xx response
- stable infrastructure error code
- correlation ID echoed in the response

## Validation Notes

- Contract, integration, and unit tests pass with `python -m pytest`
- The implementation installs from `pyproject.toml`; there is no `requirements.txt`
