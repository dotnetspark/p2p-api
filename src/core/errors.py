from __future__ import annotations

from dataclasses import dataclass


VENDOR_NOT_FOUND = "VENDOR_NOT_FOUND"
VENDOR_INACTIVE = "VENDOR_INACTIVE"
IDEMPOTENCY_KEY_CONFLICT = "IDEMPOTENCY_KEY_CONFLICT"
PURCHASE_ORDER_NOT_FOUND = "PURCHASE_ORDER_NOT_FOUND"
PURCHASE_ORDER_INVALID_STATE = "PURCHASE_ORDER_INVALID_STATE"
PURCHASE_ORDER_LINE_INVALID = "PURCHASE_ORDER_LINE_INVALID"
PURCHASE_ORDER_OVER_RECEIPT = "PURCHASE_ORDER_OVER_RECEIPT"
INVOICE_NOT_FOUND = "INVOICE_NOT_FOUND"
INVOICE_DUPLICATE_REFERENCE = "INVOICE_DUPLICATE_REFERENCE"
INVOICE_VENDOR_PO_MISMATCH = "INVOICE_VENDOR_PO_MISMATCH"
INVOICE_INVALID_STATE = "INVOICE_INVALID_STATE"
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


def idempotency_key_conflict(idempotency_key: str) -> ServiceError:
    return ServiceError(
        code=IDEMPOTENCY_KEY_CONFLICT,
        message=(
            f"Idempotency key {idempotency_key} has already been used for a different request. "
            "Retry only the original request associated with that key."
        ),
        category="business",
        retryable=False,
    )


def purchase_order_not_found(purchase_order_id: str) -> ServiceError:
    return ServiceError(
        code=PURCHASE_ORDER_NOT_FOUND,
        message=f"Purchase order {purchase_order_id} does not exist.",
        category="business",
        retryable=False,
    )


def purchase_order_invalid_state(
    purchase_order_id: str,
    current_state: str,
    required_state: str,
    action: str,
) -> ServiceError:
    return ServiceError(
        code=PURCHASE_ORDER_INVALID_STATE,
        message=(
            f"Purchase order {purchase_order_id} is in state {current_state} "
            f"but must be in state {required_state} for {action}."
        ),
        category="business",
        retryable=False,
    )


def purchase_order_line_invalid(message: str) -> ServiceError:
    return ServiceError(
        code=PURCHASE_ORDER_LINE_INVALID,
        message=message,
        category="business",
        retryable=False,
    )


def purchase_order_over_receipt(
    po_line_item_id: str,
    ordered_quantity: int,
    current_received_quantity: int,
    attempted_received_quantity: int,
) -> ServiceError:
    return ServiceError(
        code=PURCHASE_ORDER_OVER_RECEIPT,
        message=(
            f"Recording {attempted_received_quantity} units for line {po_line_item_id} "
            f"would exceed ordered quantity {ordered_quantity} from current received "
            f"quantity {current_received_quantity}."
        ),
        category="business",
        retryable=False,
    )


def invoice_not_found(invoice_id: str) -> ServiceError:
    return ServiceError(
        code=INVOICE_NOT_FOUND,
        message=f"Invoice {invoice_id} does not exist.",
        category="business",
        retryable=False,
    )


def invoice_duplicate_reference(vendor_id: str, invoice_number: str) -> ServiceError:
    return ServiceError(
        code=INVOICE_DUPLICATE_REFERENCE,
        message=(
            f"Invoice reference {invoice_number} is already registered for vendor {vendor_id}."
        ),
        category="business",
        retryable=False,
    )


def invoice_vendor_po_mismatch(vendor_id: str, purchase_order_id: str) -> ServiceError:
    return ServiceError(
        code=INVOICE_VENDOR_PO_MISMATCH,
        message=(
            f"Purchase order {purchase_order_id} does not belong to vendor {vendor_id}."
        ),
        category="business",
        retryable=False,
    )


def invoice_invalid_state(invoice_id: str, current_state: str, action: str) -> ServiceError:
    return ServiceError(
        code=INVOICE_INVALID_STATE,
        message=(
            f"Invoice {invoice_id} is in state {current_state} and cannot be used for {action}."
        ),
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
