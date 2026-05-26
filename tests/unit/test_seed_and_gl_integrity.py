from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from src.api.dependencies.error_handlers import ERROR_STATUS_BY_CODE
from src.api.schemas.invoice import InvoiceApprovalResponse
from src.core.errors import GL_ENTRIES_MISSING, GL_ENTRIES_UNBALANCED, gl_entries_missing, gl_entries_unbalanced
from src.domain.models.invoice import GLEntry, InvoiceApprovalResult
from src.domain.rules.gl_posting import gl_entries_are_balanced
from src.persistence.database import get_session_factory
from src.persistence.models.purchase_order import PurchaseOrderRow


def test_seeded_invoices_reference_seeded_purchase_orders() -> None:
    session = get_session_factory()()
    try:
        purchase_order_ids = {row.id for row in session.query(PurchaseOrderRow.id).all()}
    finally:
        session.close()

    assert {"PO-1001", "PO-1002", "PO-1003", "PO-2001"}.issubset(purchase_order_ids)


def test_gl_entries_are_balanced_accepts_more_than_two_entries_when_totals_match() -> None:
    posted_at = datetime.now(UTC)
    entries = [
        GLEntry(id="GLE-1", invoice_id="INV-1", account_code="A", debit=Decimal("50.00"), credit=Decimal("0.00"), posted_at=posted_at),
        GLEntry(id="GLE-2", invoice_id="INV-1", account_code="B", debit=Decimal("25.00"), credit=Decimal("0.00"), posted_at=posted_at),
        GLEntry(id="GLE-3", invoice_id="INV-1", account_code="C", debit=Decimal("0.00"), credit=Decimal("75.00"), posted_at=posted_at),
    ]

    assert gl_entries_are_balanced(entries) is True


def test_gl_entries_are_balanced_rejects_empty_list() -> None:
    assert gl_entries_are_balanced([]) is False


def test_gl_integrity_errors_are_non_retryable_and_map_to_500() -> None:
    missing_error = gl_entries_missing("INV-1")
    unbalanced_error = gl_entries_unbalanced("INV-1")

    assert missing_error.retryable is False
    assert unbalanced_error.retryable is False
    assert ERROR_STATUS_BY_CODE[GL_ENTRIES_MISSING] == 500
    assert ERROR_STATUS_BY_CODE[GL_ENTRIES_UNBALANCED] == 500


def test_invoice_approval_response_uses_credit_check_id_directly() -> None:
    posted_at = datetime.now(UTC)
    result = InvoiceApprovalResult(
        invoice_id="INV-1",
        invoice_status="APPROVED",
        purchase_order_id="PO-1",
        generated_gl_entries=[
            GLEntry(id="GLE-1", invoice_id="INV-1", account_code="AP_CONTROL", debit=Decimal("100.00"), credit=Decimal("0.00"), posted_at=posted_at),
            GLEntry(id="GLE-2", invoice_id="INV-1", account_code="EXPENSE", debit=Decimal("0.00"), credit=Decimal("100.00"), posted_at=posted_at),
        ],
        approved_at=posted_at,
        next_action="MARK_PAID",
        credit_check_id="CHK-123",
        should_schedule_credit_check=False,
    )

    response = InvoiceApprovalResponse.from_domain(result)

    assert response.credit_check_id == "CHK-123"