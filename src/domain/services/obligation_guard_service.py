from __future__ import annotations

from sqlalchemy.orm import Session

from src.domain.models.obligation_guard import ObligationGuardCommand, ObligationGuardResult
from src.domain.rules.vendor_eligibility import ensure_vendor_can_accept_obligations
from src.persistence.repositories.vendor_repository import VendorRepository


class ObligationGuardService:
    def __init__(self, vendor_repository: VendorRepository | None = None) -> None:
        self.vendor_repository = vendor_repository or VendorRepository()

    def guard(self, session: Session, command: ObligationGuardCommand) -> ObligationGuardResult:
        vendor = self.vendor_repository.require_by_id(session, command.vendor_id)
        ensure_vendor_can_accept_obligations(vendor)
        return ObligationGuardResult(vendor_id=vendor.id, obligations_allowed=True)
