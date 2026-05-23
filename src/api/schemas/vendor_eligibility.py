from __future__ import annotations

from src.api.schemas.common import APIModel


class VendorEligibilityResponse(APIModel):
    vendor_id: str
    vendor_name: str
    is_active: bool
    obligations_allowed: bool
    blocking_reason_code: str | None = None
    blocking_reason_message: str | None = None
