from __future__ import annotations

import json
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from src.mcp.constants import (
    URI_CONTRACT,
    URI_DOCS_E2E,
    URI_DOCS_QUICKSTART,
    URI_EXAMPLE_CREATE_INVOICE,
    URI_EXAMPLE_CREATE_PO,
    URI_EXAMPLE_FULL_WORKFLOW,
    WORKFLOW_STEPS,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


def _read_text(relative_path: str) -> str:
    path = REPO_ROOT / relative_path
    if not path.is_file():
        return f"# Resource unavailable\n\nFile not found: {relative_path}"
    return path.read_text(encoding="utf-8")


def register_resources(mcp: FastMCP) -> None:
    @mcp.resource(
        URI_DOCS_E2E,
        name="mcp_e2e_guide",
        title="MCP E2E Guide",
        description="End-to-end setup, script execution, and manual test guidance for the mounted MCP server.",
        mime_type="text/markdown",
    )
    def mcp_e2e_guide() -> str:
        return _read_text("docs/mcp-e2e.md")

    @mcp.resource(
        URI_DOCS_QUICKSTART,
        name="mcp_quickstart",
        title="MCP Quickstart",
        description="Feature quickstart notes for the MCP server tools implementation.",
        mime_type="text/markdown",
    )
    def mcp_quickstart() -> str:
        return _read_text("specs/020-mcp-server-tools/quickstart.md")

    @mcp.resource(
        URI_CONTRACT,
        name="mcp_server_tools_contract",
        title="MCP Server Tools Contract",
        description="Machine-readable contract for the MCP server tool surface.",
        mime_type="application/yaml",
    )
    def mcp_server_tools_contract() -> str:
        return _read_text("specs/020-mcp-server-tools/contracts/mcp-server-tools.yaml")

    @mcp.resource(
        URI_EXAMPLE_CREATE_PO,
        name="create_purchase_order_example",
        title="Create Purchase Order Example",
        description="Example payload for the create_purchase_order tool.",
        mime_type="application/json",
    )
    def create_purchase_order_example() -> str:
        return json.dumps(
            {
                "tool_name": "create_purchase_order",
                "arguments": {
                    "vendor_id": "V-100",
                    "line_items": [
                        {
                            "sku": "SKU-MCP-EXAMPLE-1",
                            "description": "Example line item",
                            "qty_ordered": 10,
                            "unit_cost": "12.50",
                        }
                    ],
                    "idempotency_key": "example-create-po-001",
                    "correlation_id": "example-create-po-001",
                },
            },
            indent=2,
            sort_keys=True,
        )

    @mcp.resource(
        URI_EXAMPLE_CREATE_INVOICE,
        name="create_invoice_example",
        title="Create Invoice Example",
        description="Example payload for the create_invoice tool after purchase order submission.",
        mime_type="application/json",
    )
    def create_invoice_example() -> str:
        return json.dumps(
            {
                "tool_name": "create_invoice",
                "arguments": {
                    "vendor_id": "V-100",
                    "purchase_order_id": "PO-123",
                    "invoice_number": "INV-123",
                    "invoice_amount": "125.00",
                    "idempotency_key": "example-create-invoice-001",
                    "correlation_id": "example-create-invoice-001",
                },
                "precondition": "The linked purchase order must be at least SUBMITTED.",
            },
            indent=2,
            sort_keys=True,
        )

    @mcp.resource(
        URI_EXAMPLE_FULL_WORKFLOW,
        name="full_p2p_workflow_example",
        title="Full Purchase-To-Pay Workflow Example",
        description="Ordered example sequence showing how the published tools fit together.",
        mime_type="application/json",
    )
    def full_p2p_workflow_example() -> str:
        return json.dumps(
            {
                "workflow": list(WORKFLOW_STEPS),
                "notes": [
                    "Ask for confirmation before each mutating tool call.",
                    "Carry forward purchase_order_id, po_line_item_id, invoice_id, and credit_check_id.",
                    "Use fresh idempotency keys for each distinct mutation.",
                ],
            },
            indent=2,
            sort_keys=True,
        )


__all__ = ["register_resources"]
