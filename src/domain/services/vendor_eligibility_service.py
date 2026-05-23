from __future__ import annotations

from sqlalchemy.orm import Session

from src.api.dependencies.error_handlers import AppError
from src.domain.models.vendor import VendorEligibilityResult
from src.domain.rules.vendor_eligibility import VENDOR_NOT_FOUND, build_vendor_eligibility
from src.persistence.repositories.vendor_repository import VendorRepository


class VendorEligibilityService:
    def __init__(self, vendor_repository: VendorRepository | None = None) -> None:
        self.vendor_repository = vendor_repository or VendorRepository()

    def get_eligibility(self, session: Session, vendor_id: str) -> VendorEligibilityResult:
        vendor = self.vendor_repository.get_by_id(session, vendor_id)
        if vendor is None:
            raise AppError(
                code=VENDOR_NOT_FOUND,
                message=f"Vendor {vendor_id} does not exist.",
                status_code=404,
                category="business",
                retryable=False,
            )
        return build_vendor_eligibility(vendor)
