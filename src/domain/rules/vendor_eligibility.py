from __future__ import annotations

from src.core.errors import VENDOR_INACTIVE
from src.domain.models.vendor import Vendor, VendorEligibilityResult


def build_vendor_eligibility(vendor: Vendor) -> VendorEligibilityResult:
    if vendor.is_active:
        return VendorEligibilityResult(
            vendor_id=vendor.id,
            vendor_name=vendor.name,
            is_active=True,
            obligations_allowed=True,
        )

    return VendorEligibilityResult(
        vendor_id=vendor.id,
        vendor_name=vendor.name,
        is_active=False,
        obligations_allowed=False,
        blocking_reason_code=VENDOR_INACTIVE,
        blocking_reason_message=f"Vendor {vendor.id} is inactive and cannot accept new obligations.",
    )
