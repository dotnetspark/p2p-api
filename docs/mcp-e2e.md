# MCP E2E Guide

This guide starts the mounted MCP server and runs one end-to-end purchase-to-pay flow that covers every published MCP tool.

The normal flow uses the app's standard seeded database. During my live validation I temporarily used a separate SQLite file only because the existing local `p2p.db` on this machine had stale schema from older work. That separate file was a validation workaround, not the intended default setup.

## Scope

The E2E flow covers these tools:

- `get_vendor_eligibility`
- `get_vendor_exposure`
- `create_purchase_order`
- `get_purchase_order`
- `submit_purchase_order`
- `receive_purchase_order`
- `create_invoice`
- `get_credit_check`
- `match_invoice`
- `approve_invoice`
- `pay_invoice`

Compatible MCP clients should also discover these additional server surfaces:

- prompts for guided, HITL-safe purchase-to-pay workflows
- resources for docs, contracts, and example payloads

Current prompt names:

- `guided_purchase_to_pay`
- `prepare_purchase_order_with_confirmation`
- `prepare_invoice_with_preconditions`
- `resolve_blocked_p2p_action`

Current resource URIs:

- `docs://p2p-api/mcp-e2e`
- `docs://p2p-api/mcp-quickstart`
- `contracts://p2p-api/mcp-server-tools`
- `examples://p2p-api/create-purchase-order`
- `examples://p2p-api/create-invoice`
- `examples://p2p-api/full-p2p-workflow`

## Prerequisites

- Open a terminal in the repo root.
- Use the repo virtual environment.
- Ensure port `8000` is free.

## VS Code Or Claude Terminal Workflow

These same commands work in:

- a VS Code integrated terminal
- a Claude Code terminal session rooted at this repository

### 1. Install dependencies

```powershell
.\.venv\Scripts\python -m pip install -e .[dev]
```

### 2. Start the API with MCP mounted

```powershell
.\.venv\Scripts\python -m uvicorn src.main:app --host localhost --port 8000
```

Expected result:

- REST API available at `http://localhost:8000`
- MCP endpoint available at `http://localhost:8000/mcp/`

Keep that terminal running.

### 3. Open a second terminal in the repo root

Use either VS Code or Claude again. The second terminal will run the client-side E2E script.

### 4. Run the P2P MCP E2E script

```powershell
.\.venv\Scripts\python .\scripts\p2p_mcp_e2e.py
```

Expected result:

- Every tool prints one line with `ok`, `status_code`, and `correlation_id`
- The script ends with `E2E complete`
- The script prints the final `purchase_order_id`, `invoice_id`, and `credit_check_id`

## Example Successful Output Shape

```text
get_vendor_eligibility: ok=True status_code=200 correlation_id=p2p-mcp-e2e-eligibility-...
get_vendor_exposure: ok=True status_code=200 correlation_id=p2p-mcp-e2e-exposure-...
create_purchase_order: ok=True status_code=201 correlation_id=p2p-mcp-e2e-create-po-...
get_purchase_order: ok=True status_code=200 correlation_id=p2p-mcp-e2e-get-po-...
submit_purchase_order: ok=True status_code=200 correlation_id=p2p-mcp-e2e-submit-po-...
receive_purchase_order: ok=True status_code=200 correlation_id=p2p-mcp-e2e-receive-po-...
create_invoice: ok=True status_code=201 correlation_id=p2p-mcp-e2e-create-invoice-...
get_credit_check: ok=True status_code=200 correlation_id=p2p-mcp-e2e-credit-check-...
match_invoice: ok=True status_code=200 correlation_id=p2p-mcp-e2e-match-invoice-...
approve_invoice: ok=True status_code=200 correlation_id=p2p-mcp-e2e-approve-invoice-...
pay_invoice: ok=True status_code=200 correlation_id=p2p-mcp-e2e-pay-invoice-...
E2E complete
```

## What The Script Verifies

1. The MCP server accepts client initialization over streamable HTTP.
2. Vendor read tools are callable before any mutation.
3. Purchase-order creation, retrieval, submission, and receiving all work through MCP.
4. Invoice creation returns a durable `credit_check_id`.
5. Credit-check lookup is reachable through MCP.
6. Matching, approval, and payment complete the full workflow.
7. The final invoice reaches `PAID` and the purchase order reaches `CLOSED`.

## Running Against A Different MCP URL

If the MCP endpoint is not running on the default local URL, set `P2P_MCP_URL` before running the script.

```powershell
$env:P2P_MCP_URL = "http://127.0.0.1:8000/mcp/"
.\.venv\Scripts\python .\scripts\p2p_mcp_e2e.py
```

## Troubleshooting

### Port 8000 already in use

Stop the other process or start the app on a different port and set `P2P_MCP_URL` to match.

### Local database has stale schema

If you have an older local `p2p.db`, delete it and restart the server so the current schema is recreated.

### MCP client cannot connect

Confirm the app is running and that `http://localhost:8000/mcp/` responds before running the script.

## Natural-Language Test Flow

Use this section when you want to test the MCP server manually, in plain language, without relying on the helper script. The order below covers every published MCP function.

### 1. Check that the vendor is eligible

User prompt: show me eligibility for vendor V-100
You should see a call to `get_vendor_eligibility` for vendor `V-100`.

Expected result:

- `ok = true`
- `status_code = 200`
- the payload shows that the vendor is active and allowed for new obligations

### 2. Check current vendor exposure

User prompt: show me exposure for vendor V-100
You should see a call to `get_vendor_exposure` for vendor `V-100`.

Expected result:

- `ok = true`
- `status_code = 200`
- the payload shows the vendor's current open exposure before any new purchase order or invoice is created

### 3. Create a purchase order

Call `create_purchase_order` with vendor `V-100`, one line item, an `idempotency_key`, and a `correlation_id`.

Expected result:

- `ok = true`
- `status_code = 201`
- the payload includes a new `purchase_order_id`
- the purchase order status is `DRAFT`
- the line item includes a `po_line_item_id`

Keep both `purchase_order_id` and `po_line_item_id` for the next steps.

### 4. Read the purchase order back

Call `get_purchase_order` using the new `purchase_order_id`.

Expected result:

- `ok = true`
- `status_code = 200`
- the returned purchase order matches the one you just created
- the purchase order is still in `DRAFT`

### 5. Submit the purchase order

Call `submit_purchase_order` with the `purchase_order_id`, plus a fresh `idempotency_key` and `correlation_id`.

Expected result:

- `ok = true`
- `status_code = 200`
- the purchase order status changes to `SUBMITTED`

### 6. Receive the goods

Call `receive_purchase_order` with the `purchase_order_id`, `received_by`, the saved `po_line_item_id`, the quantity received, and a fresh `idempotency_key`.

Expected result:

- `ok = true`
- `status_code = 200`
- the purchase order shows receipt progress
- the receipt is attached in the `receipts` array
- the line item shows the quantity received and remaining quantity

### 7. Create an invoice

Call `create_invoice` with vendor `V-100`, the `purchase_order_id`, a new invoice number, the invoice amount, and a fresh `idempotency_key`.

Expected result:

- `ok = true`
- `status_code = 201`
- the payload includes a new `invoice_id`
- the invoice is created in its initial status
- the payload includes a `credit_check_id`

Keep both `invoice_id` and `credit_check_id` for the next steps.

### 8. Check the credit-check status

Call `get_credit_check` with the `credit_check_id` returned from invoice creation.

Expected result:

- `ok = true`
- `status_code = 200`
- the payload shows a valid credit-check status such as `PENDING` or `COMPLETED`

### 9. Match the invoice

Call `match_invoice` with the `invoice_id` and a fresh `idempotency_key`.

Expected result:

- `ok = true`
- `status_code = 200`
- the invoice is matched successfully
- the payload exposes the match outcome and next action

### 10. Approve the invoice

Call `approve_invoice` with the `invoice_id` and a fresh `idempotency_key`.

Expected result:

- `ok = true`
- `status_code = 200`
- the invoice status changes to `APPROVED`
- the payload includes the generated GL entries
- the payload includes a `credit_check_id` for the approval path

### 11. Pay the invoice

Call `pay_invoice` with the `invoice_id` and a fresh `idempotency_key`.

Expected result:

- `ok = true`
- `status_code = 200`
- the invoice status changes to `PAID`
- the linked purchase order status changes to `CLOSED`

## Manual Completion Checklist

At the end of the manual flow, you should have validated every MCP function:

- `get_vendor_eligibility`
- `get_vendor_exposure`
- `create_purchase_order`
- `get_purchase_order`
- `submit_purchase_order`
- `receive_purchase_order`
- `create_invoice`
- `get_credit_check`
- `match_invoice`
- `approve_invoice`
- `pay_invoice`

You can also validate MCP discovery surfaces directly in a client that supports them:

- list prompts and confirm the four prompt names above are present
- get `guided_purchase_to_pay` and confirm it instructs the client to pause for confirmation before mutating tools
- list resources and confirm the docs, contract, and example URIs above are present
- read `contracts://p2p-api/mcp-server-tools` and `examples://p2p-api/full-p2p-workflow`
