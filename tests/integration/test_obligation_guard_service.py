from __future__ import annotations

import pytest

from src.api.dependencies.error_handlers import AppError
from src.domain.models.obligation_guard import ObligationGuardCommand
from src.domain.services.obligation_guard_service import ObligationGuardService
from src.persistence.database import get_session_factory


def test_obligation_guard_rechecks_current_vendor_status():
    session = get_session_factory()()
    try:
        with pytest.raises(AppError) as exc_info:
            ObligationGuardService().guard(session, ObligationGuardCommand(vendor_id="V-300"))
        assert exc_info.value.code == "VENDOR_INACTIVE"
    finally:
        session.close()
