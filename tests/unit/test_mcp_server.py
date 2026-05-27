from __future__ import annotations

from src.api.schemas.purchase_order import PurchaseOrderResponse
from src.mcp.models import PurchaseOrderToolEnvelope
from src.mcp.tools import error_result, resolve_correlation_id, success_result
from src.core.errors import purchase_order_not_found
from tests.mcp_test_utils import is_error, structured_content


def test_success_result_builds_structured_call_tool_result():
    payload = PurchaseOrderResponse(
        purchase_order_id="PO-100",
        vendor_id="V-100",
        status="DRAFT",
        line_items=[],
        receipts=[],
    )

    result = success_result(
        "create_purchase_order",
        payload,
        201,
        "corr-1",
        PurchaseOrderToolEnvelope,
    )

    assert is_error(result) is False
    assert structured_content(result) is not None
    assert structured_content(result)["ok"] is True
    assert structured_content(result)["status_code"] == 201
    assert structured_content(result)["correlation_id"] == "corr-1"
    assert structured_content(result)["data"]["purchase_order_id"] == "PO-100"


def test_error_result_marks_call_tool_result_as_error():
    result = error_result(
        "get_purchase_order",
        purchase_order_not_found("PO-404"),
        "corr-404",
        PurchaseOrderToolEnvelope,
    )

    assert is_error(result) is True
    assert structured_content(result) is not None
    assert structured_content(result)["ok"] is False
    assert structured_content(result)["status_code"] == 404
    assert structured_content(result)["error"]["code"] == "PURCHASE_ORDER_NOT_FOUND"
    assert structured_content(result)["error"]["correlation_id"] == "corr-404"


def test_resolve_correlation_id_reuses_or_generates():
    assert resolve_correlation_id("corr-existing") == "corr-existing"
    assert resolve_correlation_id(None)