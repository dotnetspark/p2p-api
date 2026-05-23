from __future__ import annotations

from src.api.dependencies.error_handlers import AppError
from src.domain.models.vendor import Vendor, VendorEligibilityResult


VENDOR_NOT_FOUND = "VENDOR_NOT_FOUND"
VENDOR_INACTIVE = "VENDOR_INACTIVE"


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


def ensure_vendor_can_accept_obligations(vendor: Vendor) -> None:
    if not vendor.is_active:
        raise AppError(
            code=VENDOR_INACTIVE,
            message=f"Vendor {vendor.id} is inactive and cannot accept new obligations.",
            status_code=409,
            category="business",
            retryable=False,
        )
