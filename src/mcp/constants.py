from __future__ import annotations

WORKFLOW_STEPS: tuple[str, ...] = (
    "get_vendor_eligibility",
    "get_vendor_exposure",
    "create_purchase_order",
    "get_purchase_order",
    "submit_purchase_order",
    "receive_purchase_order",
    "create_invoice",
    "get_credit_check",
    "match_invoice",
    "approve_invoice",
    "pay_invoice",
)

URI_DOCS_E2E = "docs://p2p-api/mcp-e2e"
URI_DOCS_QUICKSTART = "docs://p2p-api/mcp-quickstart"
URI_CONTRACT = "contracts://p2p-api/mcp-server-tools"
URI_EXAMPLE_CREATE_PO = "examples://p2p-api/create-purchase-order"
URI_EXAMPLE_CREATE_INVOICE = "examples://p2p-api/create-invoice"
URI_EXAMPLE_FULL_WORKFLOW = "examples://p2p-api/full-p2p-workflow"

__all__ = [
    "WORKFLOW_STEPS",
    "URI_CONTRACT",
    "URI_DOCS_E2E",
    "URI_DOCS_QUICKSTART",
    "URI_EXAMPLE_CREATE_INVOICE",
    "URI_EXAMPLE_CREATE_PO",
    "URI_EXAMPLE_FULL_WORKFLOW",
]
