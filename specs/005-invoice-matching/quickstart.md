# Quickstart: Invoice Matching

## Purpose

Validate the invoice registration and receipt-backed matching contract for the PoC API
using the existing Python 3.14, FastAPI, SQLAlchemy 2.x, and SQLite stack.

## Prerequisites

- Python 3.14 installed
- Project dependencies installed via editable project install
- Seed data containing at least one active vendor and one submitted purchase order
- At least one purchase order with partial and then full receipt progress available

## Assumed Seed Data

- `V-100` is active
- `PO-200` belongs to `V-100`
- `PO-200` ordered value is `1000.00`
- The current received value for `PO-200` is initially `600.00`
- Additional receipt activity can later increase the received value for `PO-200` to
  `1000.00`

## Run The API

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .[dev]
uvicorn src.main:app --reload
```

## Register An Invoice

```powershell
curl -s -X POST http://localhost:8000/invoices \
  -H "Content-Type: application/json" \
  -H "X-Correlation-ID: invoice-create-1" \
  -H "Idempotency-Key: invoice-create-1" \
  -d '{
    "vendor_id": "V-100",
    "purchase_order_id": "PO-200",
    "invoice_number": "INV-9001",
    "invoice_amount": "550.00"
  }'
```

Expected result:

- HTTP 201
- Invoice is stored once in `PENDING` status
- Response includes invoice identifier, vendor, purchase order, invoice number, amount, and `next_action = REQUEST_MATCH`

## Reject Invoice Registration Against A Draft Purchase Order

```powershell
curl -i -X POST http://localhost:8000/invoices \
  -H "Content-Type: application/json" \
  -H "X-Correlation-ID: invoice-create-draft-po" \
  -H "Idempotency-Key: invoice-create-draft-po" \
  -d '{
    "vendor_id": "V-100",
    "purchase_order_id": "PO-DRAFT-100",
    "invoice_number": "INV-DRAFT-PO-1",
    "invoice_amount": "550.00"
  }'
```

Expected result:

- HTTP 409
- Error code is `PURCHASE_ORDER_INVALID_STATE`
- The message explains that invoice registration requires a purchase order already in `SUBMITTED` or `RECEIVED`
- No invoice is created

## Reject A Duplicate Vendor Invoice Reference

```powershell
curl -i -X POST http://localhost:8000/invoices \
  -H "Content-Type: application/json" \
  -H "X-Correlation-ID: invoice-create-dup-1" \
  -H "Idempotency-Key: invoice-create-dup-1" \
  -d '{
    "vendor_id": "V-100",
    "purchase_order_id": "PO-200",
    "invoice_number": "INV-9001",
    "invoice_amount": "550.00"
  }'
```

Expected result:

- HTTP 409
- Error code is `INVOICE_DUPLICATE_REFERENCE`
- No second invoice is created for `(V-100, INV-9001)`

## Hard Reject A Match Above Received Value

```powershell
curl -i -X POST http://localhost:8000/invoices/INV-100/match \
  -H "X-Correlation-ID: invoice-match-blocked-1" \
  -H "Idempotency-Key: invoice-match-blocked-1"
```

Expected result:

- HTTP 422
- Response reports `match_status = BLOCKED`
- Response includes `received_value`, `invoice_amount`, signed `difference_amount`,
  exact `shortfall_amount`, `all_lines_fully_received = false`, and the current
  `open_lines`
- `next_action` is `WAIT_FOR_RECEIPT` when the shortfall can still be cured by future
  receipts, otherwise `CORRECT_INVOICE`

## Match Successfully With Partial Receipt Warning

```powershell
curl -i -X POST http://localhost:8000/invoices/INV-101/match \
  -H "X-Correlation-ID: invoice-match-warning-1" \
  -H "Idempotency-Key: invoice-match-warning-1"
```

Expected result:

- HTTP 202
- Response reports `match_status = MATCHED_WITH_WARNING`
- Response includes warning code `OPEN_RECEIPT_EXPOSURE`, aggregate exposure amount,
  the signed `difference_amount`, and the specific `open_lines` that remain
- Response sets `next_action = PROCEED_TO_APPROVAL` while still making the open
  exposure explicit so an agent may choose to wait
- Invoice is considered matched, but remaining purchase-order exposure is explicit

## Match Cleanly After Full Receipt

```powershell
curl -i -X POST http://localhost:8000/invoices/INV-102/match \
  -H "X-Correlation-ID: invoice-match-clean-1" \
  -H "Idempotency-Key: invoice-match-clean-1"
```

Expected result:

- HTTP 200
- Response reports `match_status = MATCHED`
- Response includes `all_lines_fully_received = true`, an empty `open_lines` list,
  and `next_action = PROCEED_TO_APPROVAL`
- No warning payload is returned
- Invoice remains in `MATCHED` status

## Re-Match After Additional Goods Receipts Arrive

```powershell
curl -i -X POST http://localhost:8000/invoices/INV-101/match \
  -H "X-Correlation-ID: invoice-match-warning-retry" \
  -H "Idempotency-Key: invoice-match-warning-1"

curl -i -X POST http://localhost:8000/invoices/INV-101/match \
  -H "X-Correlation-ID: invoice-match-warning-rematch" \
  -H "Idempotency-Key: invoice-match-warning-2"
```

Expected result:

- The first call replays the original logical outcome associated with
  `invoice-match-warning-1`
- After new goods receipts are recorded, the second call re-evaluates against the new
  receipt-backed value because it uses a fresh idempotency key
- A previously `202` outcome may become `200` once the purchase order is fully received

## Validate Business Rejections

### Vendor and purchase-order mismatch

Expected result:

- Registration is rejected when the purchase order exists but belongs to a different vendor
- Error code is `INVOICE_VENDOR_PO_MISMATCH`

### Draft purchase order used for invoice registration

Expected result:

- Registration is rejected when the purchase order exists but is still in `DRAFT`
- Error code is `PURCHASE_ORDER_INVALID_STATE`

### Conflicting idempotency-key reuse

Expected result:

- Reusing an idempotency key for a different semantic registration or match request is rejected with HTTP 409
- Error code is `IDEMPOTENCY_KEY_CONFLICT`

### Infrastructure failure handling

Expected result:

- Temporary persistence or dependency failures return retryable infrastructure errors
- Business rejections remain non-retryable and machine-distinguishable

## Validation Notes

- Contract, integration, and unit tests should pass with `python -m pytest`
- Match evaluation must use purchase-order receipt progress already recorded by the
  PO lifecycle feature rather than duplicating receipt state inside invoice logic
- Successful partial-receipt matches are warnings, not blocks
- A blocked match must not transition the invoice into `MATCHED`
- Equality between invoice amount and received value is still a warning if any lines
  remain open and becomes clean only when all lines are fully received
