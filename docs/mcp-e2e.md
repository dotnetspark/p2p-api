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
