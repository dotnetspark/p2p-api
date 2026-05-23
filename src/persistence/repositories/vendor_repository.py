from __future__ import annotations

from sqlalchemy.orm import Session

from src.api.dependencies.error_handlers import AppError
from src.domain.models.vendor import Vendor
from src.domain.rules.vendor_eligibility import VENDOR_NOT_FOUND
from src.persistence.models.vendor import VendorRow


class VendorRepository:
    def get_by_id(self, session: Session, vendor_id: str) -> Vendor | None:
        row = session.get(VendorRow, vendor_id)
        if row is None:
            return None
        return Vendor(id=row.id, name=row.name, payment_terms=row.payment_terms, is_active=row.is_active)

    def require_by_id(self, session: Session, vendor_id: str) -> Vendor:
        vendor = self.get_by_id(session, vendor_id)
        if vendor is None:
            raise AppError(
                code=VENDOR_NOT_FOUND,
                message=f"Vendor {vendor_id} does not exist.",
                status_code=404,
                category="business",
                retryable=False,
            )
        return vendor
