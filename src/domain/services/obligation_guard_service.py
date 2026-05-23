from __future__ import annotations

from sqlalchemy.orm import Session

from src.core.errors import VENDOR_INACTIVE, VENDOR_NOT_FOUND, vendor_inactive, vendor_not_found
from src.domain.models.obligation_guard import ObligationGuardCommand, ObligationGuardResult
from src.persistence.repositories.vendor_repository import VendorRepository


class ObligationGuardService:
    def __init__(self, vendor_repository: VendorRepository | None = None) -> None:
        self.vendor_repository = vendor_repository or VendorRepository()

    def guard(self, session: Session, command: ObligationGuardCommand) -> ObligationGuardResult:
        vendor = self.vendor_repository.get_by_id(session, command.vendor_id)
        if vendor is None:
            error = vendor_not_found(command.vendor_id)
            return ObligationGuardResult(
                vendor_id=command.vendor_id,
                obligations_allowed=False,
                reason_code=VENDOR_NOT_FOUND,
                reason_message=error.message,
            )
        if not vendor.is_active:
            error = vendor_inactive(vendor.id)
            return ObligationGuardResult(
                vendor_id=vendor.id,
                obligations_allowed=False,
                reason_code=VENDOR_INACTIVE,
                reason_message=error.message,
            )
        return ObligationGuardResult(vendor_id=vendor.id, obligations_allowed=True)
