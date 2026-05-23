from __future__ import annotations

from sqlalchemy.orm import Session

from src.core.errors import ServiceError, vendor_not_found
from src.core.results import Result
from src.domain.models.vendor import VendorEligibilityResult
from src.domain.rules.vendor_eligibility import build_vendor_eligibility
from src.persistence.repositories.vendor_repository import VendorRepository


class VendorEligibilityService:
    def __init__(self, vendor_repository: VendorRepository | None = None) -> None:
        self.vendor_repository = vendor_repository or VendorRepository()

    def get_eligibility(self, session: Session, vendor_id: str) -> Result[VendorEligibilityResult, ServiceError]:
        vendor = self.vendor_repository.get_by_id(session, vendor_id)
        if vendor is None:
            return Result.fail(vendor_not_found(vendor_id))
        return Result.ok(build_vendor_eligibility(vendor))
