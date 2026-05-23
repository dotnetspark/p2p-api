from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ObligationGuardCommand:
    vendor_id: str


@dataclass(frozen=True)
class ObligationGuardResult:
    vendor_id: str
    obligations_allowed: bool
    reason_code: str | None = None
    reason_message: str | None = None
