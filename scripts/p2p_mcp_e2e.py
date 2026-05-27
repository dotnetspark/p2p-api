from __future__ import annotations

import asyncio
import os
from datetime import UTC, datetime
from urllib.parse import urlsplit

import httpx
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client


def structured_content(result):
    if hasattr(result, "structuredContent"):
        return result.structuredContent
    return result.structured_content


def is_error(result) -> bool:
    if hasattr(result, "isError"):
        return result.isError
    return result.is_error


def log_step(label: str, payload: dict) -> None:
    print(f"{label}: ok={payload['ok']} status_code={payload['status_code']} correlation_id={payload['correlation_id']}")


async def main() -> None:
    endpoint = os.getenv("P2P_MCP_URL", "http://localhost:8000/mcp/")
    suffix = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
    parsed_endpoint = urlsplit(endpoint)
    base_url = f"{parsed_endpoint.scheme}://{parsed_endpoint.netloc}"

    async with httpx.AsyncClient(base_url=base_url, follow_redirects=True) as http_client:
        async with streamable_http_client(endpoint, http_client=http_client, terminate_on_close=False) as streams:
            read_stream, write_stream = streams[0], streams[1]
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()

                eligibility = await session.call_tool(
                    "get_vendor_eligibility",
                    {"vendor_id": "V-100", "correlation_id": f"p2p-mcp-e2e-eligibility-{suffix}"},
                )
                eligibility_body = structured_content(eligibility)
                if is_error(eligibility):
                    raise RuntimeError(eligibility.content[0].text)
                log_step("get_vendor_eligibility", eligibility_body)

                exposure = await session.call_tool(
                    "get_vendor_exposure",
                    {"vendor_id": "V-100", "correlation_id": f"p2p-mcp-e2e-exposure-{suffix}"},
                )
                exposure_body = structured_content(exposure)
                if is_error(exposure):
                    raise RuntimeError(exposure.content[0].text)
                log_step("get_vendor_exposure", exposure_body)

                create_po = await session.call_tool(
                    "create_purchase_order",
                    {
                        "vendor_id": "V-100",
                        "line_items": [
                            {
                                "sku": f"SKU-P2P-MCP-E2E-{suffix}",
                                "description": f"P2P MCP E2E Item {suffix}",
                                "qty_ordered": 100,
                                "unit_cost": "10.00",
                            }
                        ],
                        "idempotency_key": f"p2p-mcp-e2e-create-po-{suffix}",
                        "correlation_id": f"p2p-mcp-e2e-create-po-{suffix}",
                    },
                )
                create_po_body = structured_content(create_po)
                if is_error(create_po):
                    raise RuntimeError(create_po.content[0].text)
                log_step("create_purchase_order", create_po_body)
                purchase_order_id = create_po_body["data"]["purchase_order_id"]
                po_line_item_id = create_po_body["data"]["line_items"][0]["po_line_item_id"]

                get_po = await session.call_tool(
                    "get_purchase_order",
                    {
                        "purchase_order_id": purchase_order_id,
                        "correlation_id": f"p2p-mcp-e2e-get-po-{suffix}",
                    },
                )
                get_po_body = structured_content(get_po)
                if is_error(get_po):
                    raise RuntimeError(get_po.content[0].text)
                log_step("get_purchase_order", get_po_body)

                submit_po = await session.call_tool(
                    "submit_purchase_order",
                    {
                        "purchase_order_id": purchase_order_id,
                        "idempotency_key": f"p2p-mcp-e2e-submit-po-{suffix}",
                        "correlation_id": f"p2p-mcp-e2e-submit-po-{suffix}",
                    },
                )
                submit_po_body = structured_content(submit_po)
                if is_error(submit_po):
                    raise RuntimeError(submit_po.content[0].text)
                log_step("submit_purchase_order", submit_po_body)

                receive_po = await session.call_tool(
                    "receive_purchase_order",
                    {
                        "purchase_order_id": purchase_order_id,
                        "received_by": "warehouse-agent",
                        "line_items": [{"po_line_item_id": po_line_item_id, "qty_received": 100}],
                        "idempotency_key": f"p2p-mcp-e2e-receive-po-{suffix}",
                        "correlation_id": f"p2p-mcp-e2e-receive-po-{suffix}",
                    },
                )
                receive_po_body = structured_content(receive_po)
                if is_error(receive_po):
                    raise RuntimeError(receive_po.content[0].text)
                log_step("receive_purchase_order", receive_po_body)

                create_invoice = await session.call_tool(
                    "create_invoice",
                    {
                        "vendor_id": "V-100",
                        "purchase_order_id": purchase_order_id,
                        "invoice_number": f"INV-P2P-MCP-E2E-{suffix}",
                        "invoice_amount": "1000.00",
                        "idempotency_key": f"p2p-mcp-e2e-create-invoice-{suffix}",
                        "correlation_id": f"p2p-mcp-e2e-create-invoice-{suffix}",
                    },
                )
                create_invoice_body = structured_content(create_invoice)
                if is_error(create_invoice):
                    raise RuntimeError(create_invoice.content[0].text)
                log_step("create_invoice", create_invoice_body)
                invoice_id = create_invoice_body["data"]["invoice_id"]
                credit_check_id = create_invoice_body["data"]["credit_check_id"]

                credit_check = await session.call_tool(
                    "get_credit_check",
                    {
                        "credit_check_id": credit_check_id,
                        "correlation_id": f"p2p-mcp-e2e-credit-check-{suffix}",
                    },
                )
                credit_check_body = structured_content(credit_check)
                if is_error(credit_check):
                    raise RuntimeError(credit_check.content[0].text)
                log_step("get_credit_check", credit_check_body)

                match_invoice = await session.call_tool(
                    "match_invoice",
                    {
                        "invoice_id": invoice_id,
                        "idempotency_key": f"p2p-mcp-e2e-match-invoice-{suffix}",
                        "correlation_id": f"p2p-mcp-e2e-match-invoice-{suffix}",
                    },
                )
                match_invoice_body = structured_content(match_invoice)
                if is_error(match_invoice):
                    raise RuntimeError(match_invoice.content[0].text)
                log_step("match_invoice", match_invoice_body)

                approve_invoice = await session.call_tool(
                    "approve_invoice",
                    {
                        "invoice_id": invoice_id,
                        "idempotency_key": f"p2p-mcp-e2e-approve-invoice-{suffix}",
                        "correlation_id": f"p2p-mcp-e2e-approve-invoice-{suffix}",
                    },
                )
                approve_invoice_body = structured_content(approve_invoice)
                if is_error(approve_invoice):
                    raise RuntimeError(approve_invoice.content[0].text)
                log_step("approve_invoice", approve_invoice_body)

                pay_invoice = await session.call_tool(
                    "pay_invoice",
                    {
                        "invoice_id": invoice_id,
                        "idempotency_key": f"p2p-mcp-e2e-pay-invoice-{suffix}",
                        "correlation_id": f"p2p-mcp-e2e-pay-invoice-{suffix}",
                    },
                )
                pay_invoice_body = structured_content(pay_invoice)
                if is_error(pay_invoice):
                    raise RuntimeError(pay_invoice.content[0].text)
                log_step("pay_invoice", pay_invoice_body)

                print("E2E complete")
                print(f"purchase_order_id={purchase_order_id}")
                print(f"invoice_id={invoice_id}")
                print(f"credit_check_id={credit_check_id}")


if __name__ == "__main__":
    asyncio.run(main())