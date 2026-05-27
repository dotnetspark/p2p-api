from __future__ import annotations

import pytest

from src.persistence.database import get_session_factory
from src.persistence.models.invoice import InvoiceRow
from src.persistence.models.purchase_order import PurchaseOrderRow
from tests.mcp_test_utils import is_error, mcp_client_session, structured_content


async def _run_end_to_end_flow(session, suffix: str) -> tuple[str, str, str]:
    create_po = await session.call_tool(
        "create_purchase_order",
        {
            "vendor_id": "V-100",
            "line_items": [
                {
                    "sku": f"SKU-MCP-IT-{suffix}",
                    "description": f"Integration Item {suffix}",
                    "qty_ordered": 100,
                    "unit_cost": "10.00",
                }
            ],
            "idempotency_key": f"mcp-it-create-po-{suffix}",
            "correlation_id": f"mcp-it-create-po-{suffix}",
        },
    )
    purchase_order_id = structured_content(create_po)["data"]["purchase_order_id"]
    po_line_item_id = structured_content(create_po)["data"]["line_items"][0]["po_line_item_id"]

    await session.call_tool(
        "submit_purchase_order",
        {
            "purchase_order_id": purchase_order_id,
            "idempotency_key": f"mcp-it-submit-po-{suffix}",
            "correlation_id": f"mcp-it-submit-po-{suffix}",
        },
    )
    await session.call_tool(
        "receive_purchase_order",
        {
            "purchase_order_id": purchase_order_id,
            "received_by": "warehouse-agent",
            "line_items": [{"po_line_item_id": po_line_item_id, "qty_received": 100}],
            "idempotency_key": f"mcp-it-receive-po-{suffix}",
            "correlation_id": f"mcp-it-receive-po-{suffix}",
        },
    )
    create_invoice = await session.call_tool(
        "create_invoice",
        {
            "vendor_id": "V-100",
            "purchase_order_id": purchase_order_id,
            "invoice_number": f"INV-MCP-IT-{suffix}",
            "invoice_amount": "1000.00",
            "idempotency_key": f"mcp-it-create-invoice-{suffix}",
            "correlation_id": f"mcp-it-create-invoice-{suffix}",
        },
    )
    invoice_id = structured_content(create_invoice)["data"]["invoice_id"]
    credit_check_id = structured_content(create_invoice)["data"]["credit_check_id"]

    await session.call_tool(
        "match_invoice",
        {
            "invoice_id": invoice_id,
            "idempotency_key": f"mcp-it-match-invoice-{suffix}",
            "correlation_id": f"mcp-it-match-invoice-{suffix}",
        },
    )
    await session.call_tool(
        "approve_invoice",
        {
            "invoice_id": invoice_id,
            "idempotency_key": f"mcp-it-approve-invoice-{suffix}",
            "correlation_id": f"mcp-it-approve-invoice-{suffix}",
        },
    )
    return purchase_order_id, invoice_id, credit_check_id


@pytest.mark.anyio
async def test_mcp_end_to_end_workflow_persists_terminal_states():
    async with mcp_client_session() as session:
        purchase_order_id, invoice_id, _ = await _run_end_to_end_flow(session, "terminal")
        pay = await session.call_tool(
            "pay_invoice",
            {
                "invoice_id": invoice_id,
                "idempotency_key": "mcp-it-pay-terminal",
                "correlation_id": "mcp-it-pay-terminal",
            },
        )

    assert is_error(pay) is False
    session = get_session_factory()()
    try:
        invoice_row = session.get(InvoiceRow, invoice_id)
        purchase_order_row = session.get(PurchaseOrderRow, purchase_order_id)
        assert invoice_row is not None
        assert purchase_order_row is not None
        assert invoice_row.status == "PAID"
        assert invoice_row.paid_at is not None
        assert purchase_order_row.status == "CLOSED"
    finally:
        session.close()


@pytest.mark.anyio
async def test_mcp_replay_and_credit_check_follow_up_are_available():
    async with mcp_client_session() as session:
        purchase_order_id, _, credit_check_id = await _run_end_to_end_flow(session, "replay")
        first = await session.call_tool(
            "get_purchase_order",
            {"purchase_order_id": purchase_order_id, "correlation_id": "mcp-it-get-po-1"},
        )
        replay = await session.call_tool(
            "get_purchase_order",
            {"purchase_order_id": purchase_order_id, "correlation_id": "mcp-it-get-po-2"},
        )
        credit_check = await session.call_tool(
            "get_credit_check",
            {"credit_check_id": credit_check_id, "correlation_id": "mcp-it-credit-check-1"},
        )

    assert is_error(first) is False
    assert is_error(replay) is False
    assert structured_content(first)["data"] == structured_content(replay)["data"]
    assert is_error(credit_check) is False
    assert structured_content(credit_check)["data"]["status"] in {"PENDING", "COMPLETED"}