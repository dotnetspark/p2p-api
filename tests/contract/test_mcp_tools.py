from __future__ import annotations

import pytest

from tests.mcp_test_utils import is_error, mcp_client_session, structured_content


async def _create_approved_invoice(session, suffix: str) -> tuple[str, str]:
    create_po = await session.call_tool(
        "create_purchase_order",
        {
            "vendor_id": "V-100",
            "line_items": [
                {
                    "sku": f"SKU-MCP-{suffix}",
                    "description": f"MCP Item {suffix}",
                    "qty_ordered": 100,
                    "unit_cost": "10.00",
                }
            ],
            "idempotency_key": f"mcp-create-po-{suffix}",
            "correlation_id": f"mcp-create-po-{suffix}",
        },
    )
    purchase_order_id = structured_content(create_po)["data"]["purchase_order_id"]
    po_line_item_id = structured_content(create_po)["data"]["line_items"][0]["po_line_item_id"]

    await session.call_tool(
        "submit_purchase_order",
        {
            "purchase_order_id": purchase_order_id,
            "idempotency_key": f"mcp-submit-po-{suffix}",
            "correlation_id": f"mcp-submit-po-{suffix}",
        },
    )
    await session.call_tool(
        "receive_purchase_order",
        {
            "purchase_order_id": purchase_order_id,
            "received_by": "warehouse-agent",
            "line_items": [{"po_line_item_id": po_line_item_id, "qty_received": 100}],
            "idempotency_key": f"mcp-receive-po-{suffix}",
            "correlation_id": f"mcp-receive-po-{suffix}",
        },
    )
    create_invoice = await session.call_tool(
        "create_invoice",
        {
            "vendor_id": "V-100",
            "purchase_order_id": purchase_order_id,
            "invoice_number": f"INV-MCP-{suffix}",
            "invoice_amount": "1000.00",
            "idempotency_key": f"mcp-create-invoice-{suffix}",
            "correlation_id": f"mcp-create-invoice-{suffix}",
        },
    )
    invoice_id = structured_content(create_invoice)["data"]["invoice_id"]
    await session.call_tool(
        "match_invoice",
        {
            "invoice_id": invoice_id,
            "idempotency_key": f"mcp-match-invoice-{suffix}",
            "correlation_id": f"mcp-match-invoice-{suffix}",
        },
    )
    approve = await session.call_tool(
        "approve_invoice",
        {
            "invoice_id": invoice_id,
            "idempotency_key": f"mcp-approve-invoice-{suffix}",
            "correlation_id": f"mcp-approve-invoice-{suffix}",
        },
    )
    credit_check_id = structured_content(approve)["data"]["credit_check_id"]
    return invoice_id, credit_check_id


@pytest.mark.anyio
async def test_mcp_tools_contract_lists_expected_tools():
    async with mcp_client_session() as session:
        tools = await session.list_tools()

    tool_names = {tool.name for tool in tools.tools}
    assert {
        "get_vendor_eligibility",
        "get_vendor_exposure",
        "create_purchase_order",
        "get_purchase_order",
        "submit_purchase_order",
        "receive_purchase_order",
        "create_invoice",
        "match_invoice",
        "approve_invoice",
        "pay_invoice",
        "get_credit_check",
    }.issubset(tool_names)

    create_tool = next(tool for tool in tools.tools if tool.name == "create_purchase_order")
    assert create_tool.inputSchema["required"] == ["vendor_id", "line_items", "idempotency_key"]


@pytest.mark.anyio
async def test_mcp_create_purchase_order_contract_success():
    async with mcp_client_session() as session:
        result = await session.call_tool(
            "create_purchase_order",
            {
                "vendor_id": "V-100",
                "line_items": [
                    {
                        "sku": "SKU-MCP-CONTRACT-1",
                        "description": "Contract MCP Item",
                        "qty_ordered": 10,
                        "unit_cost": "12.50",
                    }
                ],
                "idempotency_key": "mcp-contract-create-po-1",
                "correlation_id": "mcp-contract-create-po-1",
            },
        )

    assert is_error(result) is False
    body = structured_content(result)
    assert body["ok"] is True
    assert body["status_code"] == 201
    assert body["correlation_id"] == "mcp-contract-create-po-1"
    assert body["data"]["status"] == "DRAFT"
    assert body["data"]["purchase_order_id"].startswith("PO-")


@pytest.mark.anyio
async def test_mcp_create_purchase_order_contract_requires_idempotency_key():
    async with mcp_client_session() as session:
        result = await session.call_tool(
            "create_purchase_order",
            {
                "vendor_id": "V-100",
                "line_items": [
                    {
                        "sku": "SKU-MCP-CONTRACT-2",
                        "description": "Missing key item",
                        "qty_ordered": 10,
                        "unit_cost": "12.50",
                    }
                ],
            },
        )

    assert is_error(result) is True
    assert "idempotency_key" in result.content[0].text


@pytest.mark.anyio
async def test_mcp_submit_purchase_order_contract_preserves_business_error():
    async with mcp_client_session() as session:
        result = await session.call_tool(
            "submit_purchase_order",
            {
                "purchase_order_id": "PO-DOES-NOT-EXIST",
                "idempotency_key": "mcp-contract-submit-missing",
                "correlation_id": "mcp-contract-submit-missing",
            },
        )

    assert is_error(result) is True
    body = structured_content(result)
    assert body["ok"] is False
    assert body["status_code"] == 404
    assert body["error"]["code"] == "PURCHASE_ORDER_NOT_FOUND"
    assert body["error"]["retryable"] is False
    assert body["correlation_id"] == "mcp-contract-submit-missing"


@pytest.mark.anyio
async def test_mcp_pay_invoice_contract_replays_terminal_result():
    async with mcp_client_session() as session:
        invoice_id, _ = await _create_approved_invoice(session, "pay-replay")
        first = await session.call_tool(
            "pay_invoice",
            {
                "invoice_id": invoice_id,
                "idempotency_key": "mcp-pay-replay",
                "correlation_id": "mcp-pay-replay-1",
            },
        )
        replay = await session.call_tool(
            "pay_invoice",
            {
                "invoice_id": invoice_id,
                "idempotency_key": "mcp-pay-replay",
                "correlation_id": "mcp-pay-replay-2",
            },
        )

    assert is_error(first) is False
    assert is_error(replay) is False
    first_body = structured_content(first)
    replay_body = structured_content(replay)
    assert first_body["data"]["invoice_status"] == "PAID"
    assert first_body["data"]["purchase_order_status"] == "CLOSED"
    assert first_body["data"] == replay_body["data"]