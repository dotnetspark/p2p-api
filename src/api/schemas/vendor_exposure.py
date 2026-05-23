from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from src.api.schemas.common import APIModel


class VendorExposureResponse(APIModel):
    vendor_id: str
    vendor_name: str
    as_of_timestamp: datetime
    outstanding_total_amount: Decimal
    open_invoice_count: int
    included_invoice_statuses: list[str]
