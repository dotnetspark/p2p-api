# Quickstart: Purchase Order Lifecycle

## Purpose

Validate the purchase-order lifecycle contract for the PoC API using the existing
Python 3.14, FastAPI, SQLAlchemy 2.x, and SQLite stack.

## Prerequisites

- Python 3.14 installed
- Project dependencies installed via editable project install
- Seed data containing at least one active vendor and one inactive vendor

## Assumed Seed Data

- `V-100` is active and eligible for new purchase orders
- `V-300` is inactive and must be rejected for new purchase orders

## Run The API

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .[dev]
uvicorn src.main:app --reload
```

## Create A Draft Purchase Order

```powershell
curl -s -X POST http://localhost:8000/purchase-orders \
  -H "Content-Type: application/json" \
  -H "X-Correlation-ID: po-create-1" \
  -H "Idempotency-Key: po-create-1" \
  -d '{
    "vendor_id": "V-100",
    "line_items": [
      {"sku": "SKU-1000", "description": "Cement Bags", "qty_ordered": 50, "unit_cost": 12.50},
      {"sku": "SKU-2000", "description": "Rebar", "qty_ordered": 10, "unit_cost": 48.00}
    ]
  }'
```

Expected result:

- HTTP 201
- Order status is `DRAFT`
- Returned line items reflect the ordered quantities and unit costs

## Submit The Draft Purchase Order

```powershell
curl -s -X POST http://localhost:8000/purchase-orders/PO-100/submit \
  -H "X-Correlation-ID: po-submit-1" \
  -H "Idempotency-Key: po-submit-1"
```

Expected result:

- HTTP 200
- Order status is `SUBMITTED`
- Order is now eligible for goods receipt

## Record A Partial Goods Receipt

```powershell
curl -s -X POST http://localhost:8000/purchase-orders/PO-100/receive \
  -H "Content-Type: application/json" \
  -H "X-Correlation-ID: po-receive-1" \
  -H "Idempotency-Key: po-receive-1" \
  -d '{
    "received_by": "warehouse-agent",
    "line_items": [
      {"po_line_item_id": "POL-1001", "qty_received": 20},
      {"po_line_item_id": "POL-1002", "qty_received": 4}
    ]
  }'
```

Expected result:

- HTTP 200
- Receipt event is recorded
- Returned line progress shows both cumulative received and remaining quantities
- Existing `qty_received` totals are incremented by the newly accepted receipt lines
  instead of being overwritten
- Order remains `SUBMITTED` until all lines are fully received

## Query Full Purchase Order State

```powershell
curl -s http://localhost:8000/purchase-orders/PO-100 \
  -H "X-Correlation-ID: po-query-1"
```

Expected result:

- HTTP 200
- Response includes order status, vendor reference, line-level progress, and receipt history
- Agent can determine whether invoicing should proceed or wait

## Validate Business Rejections

### Inactive vendor

```powershell
curl -i -X POST http://localhost:8000/purchase-orders \
  -H "Content-Type: application/json" \
  -H "X-Correlation-ID: po-create-inactive" \
  -H "Idempotency-Key: po-create-inactive" \
  -d '{
    "vendor_id": "V-300",
    "line_items": [
      {"sku": "SKU-1000", "description": "Cement Bags", "qty_ordered": 10, "unit_cost": 12.50}
    ]
  }'
```

Expected result:

- HTTP 409 or equivalent business rejection status
- Stable business error indicates the vendor cannot receive a new order

### Receipt before submission

Expected result:

- Goods receipt against a `DRAFT` order is rejected
- No receipt event is stored

### Over-receipt attempt

Expected result:

- Receipt that would exceed ordered quantity is rejected
- Previously accepted receipt totals remain unchanged

### Conflicting idempotency-key reuse

```powershell
curl -i -X POST http://localhost:8000/purchase-orders \
  -H "Content-Type: application/json" \
  -H "X-Correlation-ID: po-create-conflict-1" \
  -H "Idempotency-Key: po-create-conflict" \
  -d '{
    "vendor_id": "V-100",
    "line_items": [
      {"sku": "SKU-1000", "description": "Cement Bags", "qty_ordered": 50, "unit_cost": 12.50}
    ]
  }'

curl -i -X POST http://localhost:8000/purchase-orders \
  -H "Content-Type: application/json" \
  -H "X-Correlation-ID: po-create-conflict-2" \
  -H "Idempotency-Key: po-create-conflict" \
  -d '{
    "vendor_id": "V-100",
    "line_items": [
      {"sku": "SKU-2000", "description": "Rebar", "qty_ordered": 10, "unit_cost": 48.00}
    ]
  }'
```

Expected result:

- The first request succeeds with HTTP 201
- The second request is rejected with HTTP 409
- The error code is `IDEMPOTENCY_KEY_CONFLICT`
- The response marks the failure as non-retryable caller correction, not infrastructure retry

## Validation Notes

- Contract, integration, and unit tests should pass with `python -m pytest`
- The implementation should preserve receipt history while reporting cumulative line progress
- The implementation should preserve additive receipt accumulation semantics across
  multiple goods receipts for the same order line
- The implementation should not transition any order into `CLOSED`; that transition
  belongs to the later GL Posting feature after invoice payment
- The broader lifecycle still permits at most one invoice per purchase order, even
  though invoice behavior is not implemented in this feature
