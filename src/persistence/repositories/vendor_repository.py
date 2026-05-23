from __future__ import annotations

from sqlalchemy.orm import Session

from src.domain.models.vendor import Vendor
from src.persistence.models.vendor import VendorRow


class VendorRepository:
    def get_by_id(self, session: Session, vendor_id: str) -> Vendor | None:
        row = session.get(VendorRow, vendor_id)
        if row is None:
            return None
        return Vendor(id=row.id, name=row.name, payment_terms=row.payment_terms, is_active=row.is_active)
