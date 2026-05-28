from __future__ import annotations

from pathlib import Path
from typing import Annotated

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.prompts.base import AssistantMessage, UserMessage
from pydantic import Field

from src.mcp.constants import (
    URI_CONTRACT,
    URI_EXAMPLE_CREATE_INVOICE,
    URI_EXAMPLE_CREATE_PO,
    URI_EXAMPLE_FULL_WORKFLOW,
)

_TEMPLATES_DIR = Path(__file__).parent / "prompt_templates"

_ROLE_MAP = {"User": UserMessage, "Assistant": AssistantMessage}


def _load_template(name: str, **kwargs: str | int) -> list[AssistantMessage | UserMessage]:
    text = (_TEMPLATES_DIR / f"{name}.md").read_text(encoding="utf-8")
    text = text.format(**kwargs)
    messages: list[AssistantMessage | UserMessage] = []
    for block in text.split("\n## "):
        block = block.strip()
        if not block:
            continue
        role, _, body = block.partition("\n")
        role = role.lstrip("# ").strip()
        cls = _ROLE_MAP.get(role)
        if cls is not None:
            messages.append(cls(body.strip()))
    return messages


def register_prompts(mcp: FastMCP) -> None:
    @mcp.prompt(
        name="guided_purchase_to_pay",
        title="Guided Purchase-To-Pay Workflow",
        description="Walk the user through the full purchase-to-pay cycle, pausing for confirmation before every data-changing step.",
    )
    def guided_purchase_to_pay(
        vendor_id: Annotated[str, Field(description="Vendor identifier to use for the workflow")],
    ) -> list[AssistantMessage | UserMessage]:
        return _load_template(
            "guided_purchase_to_pay",
            vendor_id=vendor_id,
            uri_contract=URI_CONTRACT,
            uri_example_full_workflow=URI_EXAMPLE_FULL_WORKFLOW,
        )

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
        return _load_template(
            "prepare_purchase_order_with_confirmation",
            vendor_id=vendor_id,
            sku=sku,
            description=description,
            qty_ordered=str(qty_ordered),
            unit_cost=unit_cost,
            uri_example_create_po=URI_EXAMPLE_CREATE_PO,
        )

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
        return _load_template(
            "prepare_invoice_with_preconditions",
            vendor_id=vendor_id,
            purchase_order_id=purchase_order_id,
            invoice_number=invoice_number,
            invoice_amount=invoice_amount,
            uri_example_create_invoice=URI_EXAMPLE_CREATE_INVOICE,
        )

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
        return _load_template(
            "resolve_blocked_p2p_action",
            tool_name=tool_name,
            error_code=error_code,
            message=message,
            uri_contract=URI_CONTRACT,
            uri_example_full_workflow=URI_EXAMPLE_FULL_WORKFLOW,
        )


__all__ = ["register_prompts"]
