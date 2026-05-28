from __future__ import annotations

from mcp.server.fastmcp import FastMCP

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


def build_mcp_server() -> FastMCP:
    mcp = FastMCP(
        "p2p-api",
        instructions=(
            "Purchase-to-pay workflow tools backed by the existing p2p-api business logic. "
            "Mutating tools require caller-supplied idempotency keys."
        ),
    )
    mcp.settings.streamable_http_path = "/"
    mcp.settings.json_response = True
    mcp.settings.stateless_http = True

    mcp.add_tool(get_vendor_eligibility_tool, name="get_vendor_eligibility")
    mcp.add_tool(get_vendor_exposure_tool, name="get_vendor_exposure")
    mcp.add_tool(create_purchase_order_tool, name="create_purchase_order")
    mcp.add_tool(get_purchase_order_tool, name="get_purchase_order")
    mcp.add_tool(submit_purchase_order_tool, name="submit_purchase_order")
    mcp.add_tool(receive_purchase_order_tool, name="receive_purchase_order")
    mcp.add_tool(create_invoice_tool, name="create_invoice")
    mcp.add_tool(match_invoice_tool, name="match_invoice")
    mcp.add_tool(approve_invoice_tool, name="approve_invoice")
    mcp.add_tool(pay_invoice_tool, name="pay_invoice")
    mcp.add_tool(get_credit_check_tool, name="get_credit_check")

    register_prompts(mcp)
    register_resources(mcp)

    return mcp


mcp_server = build_mcp_server()


__all__ = ["build_mcp_server", "mcp_server"]