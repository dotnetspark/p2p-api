from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

from src.domain.models.invoice import AP_CONTROL_ACCOUNT, GLEntry, UNCLASSIFIED_EXPENSE_ACCOUNT
from src.domain.models.vendor import Vendor


VENDOR_CATEGORY_BUILDING_SUPPLY = "BUILDING_SUPPLY"
VENDOR_CATEGORY_AGGREGATES = "AGGREGATES"
VENDOR_CATEGORY_TIMBER = "TIMBER"

EXPENSE_ACCOUNT_BY_CATEGORY = {
    VENDOR_CATEGORY_BUILDING_SUPPLY: "EXPENSE_BUILDING_SUPPLY",
    VENDOR_CATEGORY_AGGREGATES: "EXPENSE_AGGREGATES",
    VENDOR_CATEGORY_TIMBER: "EXPENSE_TIMBER",
}


def derive_vendor_category(vendor: Vendor) -> str | None:
    normalized_name = vendor.name.strip().lower()
    if "building supply" in normalized_name:
        return VENDOR_CATEGORY_BUILDING_SUPPLY
    if "aggregates" in normalized_name:
        return VENDOR_CATEGORY_AGGREGATES
    if "timber" in normalized_name:
        return VENDOR_CATEGORY_TIMBER
    return None


def resolve_expense_account_code(vendor: Vendor) -> str:
    vendor_category = derive_vendor_category(vendor)
    if vendor_category is None:
        return UNCLASSIFIED_EXPENSE_ACCOUNT
    return EXPENSE_ACCOUNT_BY_CATEGORY.get(vendor_category, UNCLASSIFIED_EXPENSE_ACCOUNT)


def build_balanced_gl_entries(
    invoice_id: str,
    invoice_amount: Decimal,
    expense_account_code: str,
    posted_at: datetime | None = None,
) -> list[GLEntry]:
    posting_time = posted_at or datetime.now(UTC)
    normalized_amount = invoice_amount.quantize(Decimal("0.01"))
    return [
        GLEntry(
            id=f"GLE-{uuid4().hex[:8].upper()}",
            invoice_id=invoice_id,
            account_code=expense_account_code,
            debit=normalized_amount,
            credit=Decimal("0.00"),
            posted_at=posting_time,
        ),
        GLEntry(
            id=f"GLE-{uuid4().hex[:8].upper()}",
            invoice_id=invoice_id,
            account_code=AP_CONTROL_ACCOUNT,
            debit=Decimal("0.00"),
            credit=normalized_amount,
            posted_at=posting_time,
        ),
    ]


def gl_entries_are_balanced(gl_entries: list[GLEntry]) -> bool:
    if not gl_entries:
        return False
    total_debit = sum((entry.debit for entry in gl_entries), Decimal("0.00")).quantize(Decimal("0.01"))
    total_credit = sum((entry.credit for entry in gl_entries), Decimal("0.00")).quantize(Decimal("0.01"))
    return total_debit == total_credit