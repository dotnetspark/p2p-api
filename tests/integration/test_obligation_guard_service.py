from __future__ import annotations

from src.domain.models.obligation_guard import ObligationGuardCommand
from src.domain.services.obligation_guard_service import ObligationGuardService
from src.persistence.database import get_session_factory


def test_obligation_guard_rechecks_current_vendor_status():
    session = get_session_factory()()
    try:
        result = ObligationGuardService().guard(session, ObligationGuardCommand(vendor_id="V-300"))
        assert result.obligations_allowed is False
        assert result.reason_code == "VENDOR_INACTIVE"
    finally:
        session.close()
