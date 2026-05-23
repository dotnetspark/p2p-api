from __future__ import annotations

from src.domain.models.obligation_guard import ObligationGuardCommand
from src.domain.services.obligation_guard_service import ObligationGuardService
from src.persistence.database import get_session_factory


def test_obligation_guard_allows_active_vendor():
    session = get_session_factory()()
    try:
        result = ObligationGuardService().guard(session, ObligationGuardCommand(vendor_id="V-100"))
        assert result.obligations_allowed is True
        assert result.reason_code is None
    finally:
        session.close()


def test_obligation_guard_rejects_inactive_vendor():
    session = get_session_factory()()
    try:
        result = ObligationGuardService().guard(session, ObligationGuardCommand(vendor_id="V-300"))
        assert result.obligations_allowed is False
        assert result.reason_code == "VENDOR_INACTIVE"
    finally:
        session.close()
