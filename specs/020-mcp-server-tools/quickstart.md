# Quickstart: MCP Server Tools

## Purpose

Validate that the P2P API can be discovered and executed through MCP tools without
issuing raw HTTP requests directly, while preserving idempotency, correlation IDs,
and machine-readable business failures.

## Prerequisites

- Python 3.14 installed
- Project dependencies installed into the repo virtual environment
- Seed data available for vendor `V-100`
- The MCP Python SDK installed through the project dependency set

## Run The Service With MCP Mounted

```powershell
c:/Users/ylrre/source/repos/p2p-api/.venv/Scripts/python.exe -m pip install -e .[dev]
c:/Users/ylrre/source/repos/p2p-api/.venv/Scripts/python.exe -m uvicorn src.main:app --reload
```

Expected result:

- The existing REST API remains available on `http://localhost:8000`
- The mounted MCP endpoint is available on `http://localhost:8000/mcp`

## Discover The Available Tools

Run this script from the repository root:

```python
import asyncio

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client


async def main() -> None:
    async with streamable_http_client("http://localhost:8000/mcp") as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            tools = await session.list_tools()
            print(sorted(tool.name for tool in tools.tools))


asyncio.run(main())
```

Expected result:

- The tool list includes the current workflow operations, including:
  - `get_vendor_eligibility`
  - `get_vendor_exposure`
  - `create_purchase_order`
  - `get_purchase_order`
  - `submit_purchase_order`
  - `receive_purchase_order`
  - `create_invoice`
  - `match_invoice`
  - `approve_invoice`
  - `pay_invoice`
  - `get_credit_check`

## Execute A Purchase Order Through MCP

```python
import asyncio

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client


def structured(result):
    return getattr(result, "structuredContent", None) or getattr(result, "structured_content", None)


async def main() -> None:
    async with streamable_http_client("http://localhost:8000/mcp") as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            created = await session.call_tool(
                "create_purchase_order",
                arguments={
                    "vendor_id": "V-100",
                    "line_items": [
                        {
                            "sku": "SKU-1000",
                            "description": "Cement Bags",
                            "qty_ordered": 10,
                            "unit_cost": "12.50",
                        }
                    ],
                    "idempotency_key": "mcp-po-create-1",
                    "correlation_id": "mcp-po-create-1",
                },
            )
            print(structured(created))


asyncio.run(main())
```

Expected result:

- The tool returns a structured envelope with:
  - `ok = true`
  - `status_code = 201`
  - `correlation_id = "mcp-po-create-1"`
  - `data.purchase_order_id` populated
  - `data.status = "DRAFT"`

## Run One End-To-End Purchase-To-Pay Flow

Continue the same session or reconnect and execute the remaining tools in order:

1. `submit_purchase_order`
2. `receive_purchase_order`
3. `create_invoice`
4. `match_invoice`
5. `approve_invoice`
6. `pay_invoice`

Expected result:

- Each tool returns `ok = true`
- The business payload inside `data` matches the existing REST response semantics
- `create_invoice` and `approve_invoice` keep returning `credit_check_id`
- `approve_invoice` returns `generated_gl_entries`
- `pay_invoice` returns final invoice and purchase-order statuses

## Validate Replay Safety

Replay one mutating tool with the same `idempotency_key`, for example
`approve_invoice`.

Expected result:

- The replayed tool still returns a success envelope
- The logical business outcome matches the first successful call
- No duplicate side effect is introduced
- Any follow-up handle such as `credit_check_id` matches the original logical result

## Validate A Machine-Readable Failure

Call `approve_invoice` for an invoice that has not been matched yet, or call
`submit_purchase_order` against a non-existent purchase order.

Expected result:

- The MCP result is marked as an error
- The structured payload contains:
  - `ok = false`
  - `status_code` matching the REST error mapping, such as `404` or `409`
  - `error.code`, `error.category`, `error.retryable`, and `error.message`
  - `correlation_id` on both the top-level envelope and nested error

## Validate Read-Only Discovery And Follow-Up Queries

Use the read tools after the flow completes:

1. `get_purchase_order`
2. `get_vendor_exposure`
3. `get_credit_check`

Expected result:

- Read tools do not require `idempotency_key`
- The returned data payloads remain the same shape as the published REST responses
- `get_credit_check` allows the agent to inspect async credit evaluation without
  consulting logs or direct database state

## Validation Notes

- The MCP server is general-purpose and can be consumed by LangGraph, Claude Code,
  or any other MCP-compatible client
- The REST API remains the source contract for business semantics
- The MCP layer adds discovery and invocation ergonomics, not a second workflow
  implementation
