from __future__ import annotations

from typing import Annotated

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.prompts.base import AssistantMessage, UserMessage
from pydantic import Field

from src.mcp.constants import URI_CONTRACT, URI_EXAMPLE_CREATE_INVOICE, URI_EXAMPLE_CREATE_PO, URI_EXAMPLE_FULL_WORKFLOW


def register_prompts(mcp: FastMCP) -> None:
    @mcp.prompt(
        name="guided_purchase_to_pay",
        title="Guided Purchase-To-Pay Workflow",
        description="Walk the user through the full purchase-to-pay cycle, pausing for confirmation before every data-changing step.",
    )
    def guided_purchase_to_pay(
        vendor_id: Annotated[str, Field(description="Vendor identifier to use for the workflow")],
    ) -> list[AssistantMessage | UserMessage]:
        return [
            UserMessage(
                f"Walk me through the full purchase-to-pay cycle for vendor {vendor_id}, "
                "step by step, and pause for my go-ahead before making any changes."
            ),
            AssistantMessage(
                f"I'll guide you through the complete purchase-to-pay process for vendor {vendor_id}. "
                "We'll start by verifying that the vendor is active and eligible, then review their current "
                "financial exposure. Once confirmed, I'll help you raise a purchase order, submit it, record "
                "goods receipt when the items arrive, and then process an invoice through credit assessment, "
                "three-way matching, approval, and final payment. "
                "I'll pause and explain exactly what I'm about to do before every step that changes data, "
                "and wait for your confirmation before proceeding."
            ),
            AssistantMessage(
                "I'll keep the key identifiers in context throughout — purchase order, line item, invoice, "
                "and credit check references — so you don't need to track them manually."
            ),
            AssistantMessage(
                "If a step is blocked by a business rule I'll explain what precondition wasn't met and "
                "suggest the next valid action rather than retrying automatically. "
                f"For the formal tool contract or a worked end-to-end example, I can pull up "
                f"{URI_CONTRACT} or {URI_EXAMPLE_FULL_WORKFLOW}."
            ),
        ]

    @mcp.prompt(
        name="prepare_purchase_order_with_confirmation",
        title="Prepare Purchase Order With Confirmation",
        description="Collect purchase order details from the user and enforce a confirmation step before raising the draft.",
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
                f"I'd like to place an order for {qty_ordered} units of {sku} — '{description}' "
                f"at {unit_cost} each — with vendor {vendor_id}."
            ),
            AssistantMessage(
                f"Before I create anything, let me check that vendor {vendor_id} is currently active "
                "and eligible to receive new obligations. I may also review their outstanding exposure "
                "if you'd like that context first."
            ),
            AssistantMessage(
                f"Once eligibility is confirmed, I'll summarise the order — vendor {vendor_id}, "
                f"{qty_ordered} × {sku} ({description}) at {unit_cost} each — and ask for your "
                "confirmation before raising the draft. I'll include a unique idempotency key so the "
                "request is safe to retry. After creation I'll keep the purchase order ID and line item ID "
                "ready for the submit and receive steps."
            ),
            AssistantMessage(
                f"If you'd like to see a concrete example of a purchase order payload before we proceed, "
                f"I can pull one up from {URI_EXAMPLE_CREATE_PO}."
            ),
        ]

    @mcp.prompt(
        name="prepare_invoice_with_preconditions",
        title="Prepare Invoice With Preconditions",
        description="Guide invoice creation only after confirming the linked purchase order is in a valid state.",
    )
    def prepare_invoice_with_preconditions(
        vendor_id: Annotated[str, Field(description="Vendor identifier on the invoice")],
        purchase_order_id: Annotated[str, Field(description="Purchase order identifier linked to the invoice")],
        invoice_number: Annotated[str, Field(description="Vendor-provided invoice number")],
        invoice_amount: Annotated[str, Field(description="Invoice amount as a decimal string")],
    ) -> list[AssistantMessage | UserMessage]:
        return [
            UserMessage(
                f"I need to register invoice {invoice_number} for purchase order {purchase_order_id} "
                f"from vendor {vendor_id}, for the amount of {invoice_amount}."
            ),
            AssistantMessage(
                f"Before I raise the invoice, I'll check the current state of purchase order {purchase_order_id}. "
                "The invoice can only be created once the order has been submitted; if goods have already "
                "been received I'll include that context so you have the full picture."
            ),
            AssistantMessage(
                f"Once the preconditions are satisfied, I'll confirm the full details — vendor {vendor_id}, "
                f"order {purchase_order_id}, invoice {invoice_number}, amount {invoice_amount}, and an "
                "idempotency key — and ask for your approval before registering the invoice. After that I'll "
                "keep the invoice ID and credit check ID in context so we can progress through matching, "
                "approval, and payment."
            ),
            AssistantMessage(
                f"If you'd like to see what a typical invoice payload looks like, I can pull up an example "
                f"from {URI_EXAMPLE_CREATE_INVOICE}."
            ),
        ]

    @mcp.prompt(
        name="resolve_blocked_p2p_action",
        title="Resolve Blocked P2P Action",
        description="Explain a failed purchase-to-pay step in business terms and propose the next valid move without auto-retrying.",
    )
    def resolve_blocked_p2p_action(
        tool_name: Annotated[str, Field(description="Name of the tool that failed or was blocked")],
        error_code: Annotated[str, Field(description="Business error code returned by the tool")],
        message: Annotated[str, Field(description="Human-readable error message to explain")],
    ) -> list[AssistantMessage | UserMessage]:
        return [
            UserMessage(
                f"Something went wrong during a purchase-to-pay step. "
                f"The '{tool_name}' action couldn't complete — it came back with '{error_code}': {message}"
            ),
            AssistantMessage(
                "That error means a business rule wasn't satisfied. Let me explain what happened in plain "
                "terms and what needs to be true before we can move forward. I won't retry the same action "
                "automatically — instead I'll tell you exactly what the next valid step is and let you "
                "decide how to proceed."
            ),
            AssistantMessage(
                "If you need the formal contract or a worked end-to-end example to understand the expected "
                f"flow, I can pull those up from {URI_CONTRACT} or {URI_EXAMPLE_FULL_WORKFLOW}."
            ),
        ]


__all__ = ["register_prompts"]
