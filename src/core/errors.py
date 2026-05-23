from __future__ import annotations

from dataclasses import dataclass


VENDOR_NOT_FOUND = "VENDOR_NOT_FOUND"
VENDOR_INACTIVE = "VENDOR_INACTIVE"
DEPENDENCY_TEMPORARILY_UNAVAILABLE = "DEPENDENCY_TEMPORARILY_UNAVAILABLE"


@dataclass(frozen=True)
class ServiceError:
    code: str
    message: str
    category: str
    retryable: bool = False


def vendor_not_found(vendor_id: str) -> ServiceError:
    return ServiceError(
        code=VENDOR_NOT_FOUND,
        message=f"Vendor {vendor_id} does not exist.",
        category="business",
        retryable=False,
    )


def vendor_inactive(vendor_id: str) -> ServiceError:
    return ServiceError(
        code=VENDOR_INACTIVE,
        message=f"Vendor {vendor_id} is inactive and cannot accept new obligations.",
        category="business",
        retryable=False,
    )


def dependency_temporarily_unavailable() -> ServiceError:
    return ServiceError(
        code=DEPENDENCY_TEMPORARILY_UNAVAILABLE,
        message="A temporary dependency failure prevented request completion.",
        category="infrastructure",
        retryable=True,
    )
