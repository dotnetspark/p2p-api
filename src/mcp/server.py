from __future__ import annotations

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from src.mcp.prompts import register_prompts
from src.mcp.resources import register_resources
from src.mcp.tools import (
    approve_invoice_tool,
    create_invoice_tool,
    create_purchase_order_tool,
    get_credit_check_tool,
    get_purchase_order_tool,
    get_vendor_eligibility_tool,
    get_vendor_exposure_tool,
    match_invoice_tool,
    pay_invoice_tool,
    receive_purchase_order_tool,
    submit_purchase_order_tool,
)

_READ_ONLY = ToolAnnotations(readOnlyHint=True)
_MUTATING = ToolAnnotations(readOnlyHint=False, destructiveHint=False, idempotentHint=True)
_DESTRUCTIVE = ToolAnnotations(readOnlyHint=False, destructiveHint=True, idempotentHint=True)


def build_mcp_server() -> FastMCP:
    mcp = FastMCP(
        "p2p-api",
        instructions=(
            "Purchase-to-pay workflow server. "
            "Read-only tools (safe to call freely): get_vendor_eligibility, get_vendor_exposure, "
            "get_purchase_order, get_credit_check. "
            "Mutating tools (all require an idempotency_key, safe to replay): create_purchase_order, "
            "submit_purchase_order, receive_purchase_order, create_invoice, match_invoice, approve_invoice. "
            "Terminal mutation (destructive — closes the linked purchase order): pay_invoice. "
            "Always confirm with the user before calling any mutating tool."
        ),
    )
    mcp.settings.streamable_http_path = "/"
    mcp.settings.json_response = True
    mcp.settings.stateless_http = True

    mcp.add_tool(get_vendor_eligibility_tool, name="get_vendor_eligibility", annotations=_READ_ONLY)
    mcp.add_tool(get_vendor_exposure_tool, name="get_vendor_exposure", annotations=_READ_ONLY)
    mcp.add_tool(create_purchase_order_tool, name="create_purchase_order", annotations=_MUTATING)
    mcp.add_tool(get_purchase_order_tool, name="get_purchase_order", annotations=_READ_ONLY)
    mcp.add_tool(submit_purchase_order_tool, name="submit_purchase_order", annotations=_MUTATING)
    mcp.add_tool(receive_purchase_order_tool, name="receive_purchase_order", annotations=_MUTATING)
    mcp.add_tool(create_invoice_tool, name="create_invoice", annotations=_MUTATING)
    mcp.add_tool(match_invoice_tool, name="match_invoice", annotations=_MUTATING)
    mcp.add_tool(approve_invoice_tool, name="approve_invoice", annotations=_MUTATING)
    mcp.add_tool(pay_invoice_tool, name="pay_invoice", annotations=_DESTRUCTIVE)
    mcp.add_tool(get_credit_check_tool, name="get_credit_check", annotations=_READ_ONLY)

    register_prompts(mcp)
    register_resources(mcp)

    return mcp


mcp_server = build_mcp_server()


__all__ = ["build_mcp_server", "mcp_server"]