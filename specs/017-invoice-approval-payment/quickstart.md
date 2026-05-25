# Quickstart: Invoice Approval and Payment

## Purpose

Validate the invoice approval, GL-posting, and payment-completion contract for the
PoC P2P API using the existing Python 3.14, FastAPI, SQLAlchemy 2.x, and SQLite
stack.

## Prerequisites

- Python 3.14 installed
- Project dependencies installed via editable project install
- Seed or test data containing at least one matched invoice linked to a receipted
  purchase order
- Vendor classification data or fallback behavior available for expense-account
  selection

## Run The API

```powershell
c:/Users/ylrre/source/repos/p2p-api/.venv/Scripts/python.exe -m pip install -e .[dev]
c:/Users/ylrre/source/repos/p2p-api/.venv/Scripts/python.exe -m uvicorn src.main:app --reload
```

## Approve A Matched Invoice

```powershell
curl -i -X POST http://localhost:8000/invoices/INV-APP-200/approve \
  -H "X-Correlation-ID: invoice-approve-1" \
  -H "Idempotency-Key: invoice-approve-1"
```

Expected result:

- HTTP 200
- Invoice status becomes `APPROVED`
- Response contains exactly two generated GL entry identifiers
- One GL entry represents the payable obligation using `AP_CONTROL`
- One GL entry represents the expense using the repo's deterministic vendor
  classification rule, for example `EXPENSE_BUILDING_SUPPLY` for `ACME Building Supply`,
  or `UNCLASSIFIED_EXPENSE` when no category rule matches
- Response tells the agent that the next step is to mark the invoice paid

## Reject Approval For An Unmatched Invoice

```powershell
curl -i -X POST http://localhost:8000/invoices/INV-APP-201/approve \
  -H "X-Correlation-ID: invoice-approve-invalid" \
  -H "Idempotency-Key: invoice-approve-invalid"
```

Expected result:

- HTTP 409
- Error code indicates the invoice is in the wrong state for approval
- No GL entries are created

## Replay An Approval Safely

```powershell
curl -i -X POST http://localhost:8000/invoices/INV-APP-200/approve \
  -H "X-Correlation-ID: invoice-approve-replay-1" \
  -H "Idempotency-Key: invoice-approve-1"
```

Expected result:

- Same logical success outcome is replayed
- No duplicate GL entries are created

## Mark An Approved Invoice Paid

```powershell
curl -i -X POST http://localhost:8000/invoices/INV-APP-200/pay \
  -H "X-Correlation-ID: invoice-pay-1" \
  -H "Idempotency-Key: invoice-pay-1"
```

Expected result:

- HTTP 200
- Invoice status becomes `PAID`
- Linked purchase order status becomes `CLOSED`
- Payment succeeds only after approval and against a purchase order that is already in
  the receipted `RECEIVED` state
- Response indicates that the lifecycle is complete

## Reject Payment Before Approval

```powershell
curl -i -X POST http://localhost:8000/invoices/INV-APP-202/pay \
  -H "X-Correlation-ID: invoice-pay-invalid" \
  -H "Idempotency-Key: invoice-pay-invalid"
```

Expected result:

- HTTP 409
- Error code indicates the invoice is in the wrong state for payment
- Invoice remains unpaid and purchase order remains open

## Validation Notes

- Approval must generate exactly two GL entries and those entries must balance
- Missing vendor category mapping must fall back safely to an unclassified expense
  account rather than fail approval
- Payment must not be allowed before approval
- Payment closes only a receipted purchase order; it does not override earlier PO
  state rules
- Payment completes the invoice lifecycle and closes the linked purchase order for the
  current repository scope
- Contract and integration tests should pass with `c:/Users/ylrre/source/repos/p2p-api/.venv/Scripts/python.exe -m pytest`
