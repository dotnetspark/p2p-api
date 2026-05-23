from __future__ import annotations

import pytest

from src.api.dependencies.error_handlers import AppError
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
        with pytest.raises(AppError) as exc_info:
            ObligationGuardService().guard(session, ObligationGuardCommand(vendor_id="V-300"))
        assert exc_info.value.code == "VENDOR_INACTIVE"
        assert exc_info.value.status_code == 409
    finally:
        session.close()
