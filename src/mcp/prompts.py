from __future__ import annotations

from typing import Annotated

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.prompts.base import AssistantMessage, UserMessage
from pydantic import Field


def register_prompts(mcp: FastMCP) -> None:
    @mcp.prompt(
        name="guided_purchase_to_pay",
        title="Guided Purchase-To-Pay Workflow",
        description="Walk the client through the full purchase-to-pay sequence without silently advancing past human approval points.",
    )
    def guided_purchase_to_pay(
        vendor_id: Annotated[str, Field(description="Vendor identifier to use for the workflow")],
    ) -> list[AssistantMessage | UserMessage]:
        return [
            UserMessage(
                f"Guide me through the purchase-to-pay workflow for vendor {vendor_id}. "
                "Do not skip steps or chain together mutating actions without confirmation."
            ),
            AssistantMessage(
                "Use this sequence: 1) get_vendor_eligibility, 2) get_vendor_exposure, "
                "3) create_purchase_order, 4) get_purchase_order, 5) submit_purchase_order, "
                "6) receive_purchase_order, 7) create_invoice, 8) get_credit_check, "
                "9) match_invoice, 10) approve_invoice, 11) pay_invoice."
            ),
            AssistantMessage(
                "Before every mutating tool call, explain the intended action, ask for confirmation, "
                "and wait. Keep the current identifiers in context: purchase_order_id, po_line_item_id, "
                "invoice_id, and credit_check_id."
            ),
            AssistantMessage(
                "If a step is blocked, explain the business precondition that failed, propose the next valid tool, "
                "and refer to these resources when useful: docs://p2p-api/mcp-e2e, "
                "contracts://p2p-api/mcp-server-tools, and examples://p2p-api/full-p2p-workflow."
            ),
        ]

    @mcp.prompt(
        name="prepare_purchase_order_with_confirmation",
        title="Prepare Purchase Order With Confirmation",
        description="Gather the fields needed for create_purchase_order and enforce a confirmation step before mutation.",
    )
    def prepare_purchase_order_with_confirmation(
        vendor_id: Annotated[str, Field(description="Vendor identifier for the purchase order")],
        sku: Annotated[str, Field(description="SKU for the requested item")],
        description: Annotated[str, Field(description="Human-readable line item description")],
        qty_ordered: Annotated[int, Field(description="Ordered quantity for the line item")],
        unit_cost: Annotated[str, Field(description="Unit cost as a decimal string, for example 10.00")],
    ) -> list[AssistantMessage | UserMessage]:
        return [
            UserMessage(
                f"Prepare a draft purchase order for vendor {vendor_id} with {qty_ordered} units of {sku} "
                f"described as '{description}' at {unit_cost} each."
            ),
            AssistantMessage(
                "First confirm vendor readiness with get_vendor_eligibility and optionally get_vendor_exposure "
                "if the user needs current liability context."
            ),
            AssistantMessage(
                "Before calling create_purchase_order, restate the payload, confirm the user wants to create it now, "
                "and ensure an idempotency_key is present. After creation, retain purchase_order_id and po_line_item_id "
                "for later submit and receive steps."
            ),
            AssistantMessage(
                "If the user asks for an example payload, read examples://p2p-api/create-purchase-order."
            ),
        ]

    @mcp.prompt(
        name="prepare_invoice_with_preconditions",
        title="Prepare Invoice With Preconditions",
        description="Guide invoice creation only after the linked purchase order satisfies the required state.",
    )
    def prepare_invoice_with_preconditions(
        vendor_id: Annotated[str, Field(description="Vendor identifier on the invoice")],
        purchase_order_id: Annotated[str, Field(description="Purchase order identifier linked to the invoice")],
        invoice_number: Annotated[str, Field(description="Vendor-provided invoice number")],
        invoice_amount: Annotated[str, Field(description="Invoice amount as a decimal string")],
    ) -> list[AssistantMessage | UserMessage]:
        return [
            UserMessage(
                f"Help me register invoice {invoice_number} for purchase order {purchase_order_id} and vendor {vendor_id}."
            ),
            AssistantMessage(
                "Check get_purchase_order first. The invoice path is valid only when the purchase order is at least SUBMITTED. "
                "If goods have already arrived, include that context before asking to create the invoice."
            ),
            AssistantMessage(
                "Before create_invoice, restate vendor_id, purchase_order_id, invoice_number, invoice_amount, and idempotency_key. "
                "After creation, keep invoice_id and credit_check_id in context so the next steps can use get_credit_check, "
                "match_invoice, and approve_invoice."
            ),
            AssistantMessage(
                "If the user needs a concrete payload shape, read examples://p2p-api/create-invoice."
            ),
        ]

    @mcp.prompt(
        name="resolve_blocked_p2p_action",
        title="Resolve Blocked P2P Action",
        description="Explain a blocked or failed purchase-to-pay step and suggest the next valid move without auto-retrying.",
    )
    def resolve_blocked_p2p_action(
        tool_name: Annotated[str, Field(description="Name of the tool that failed or was blocked")],
        error_code: Annotated[str, Field(description="Business error code returned by the tool")],
        message: Annotated[str, Field(description="Human-readable error message to explain")],
    ) -> list[AssistantMessage | UserMessage]:
        return [
            UserMessage(f"A purchase-to-pay action failed in {tool_name} with {error_code}: {message}"),
            AssistantMessage(
                "Explain the business rule in plain language, do not retry automatically, and name the next valid tool or user decision."
            ),
            AssistantMessage(
                "If the client needs the formal contract or a worked example, direct it to "
                "contracts://p2p-api/mcp-server-tools and examples://p2p-api/full-p2p-workflow."
            ),
        ]


__all__ = ["register_prompts"]