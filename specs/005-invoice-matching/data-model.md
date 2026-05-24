# Data Model: Invoice Matching

## Overview

This feature models invoice registration and receipt-backed match evaluation against
an existing purchase order. The invoice is persisted once, then evaluated one or more
times as goods receipts accumulate. Successful matches may occur while receipt
exposure remains open, but blocked matches must never allow the invoice to progress
as supported.

## Entities

### Invoice

**Purpose**: Represents a vendor billing document linked to one purchase order and
anchors the invoice workflow within this feature.

**Fields**:

- `id`: Stable invoice identifier
- `vendor_id`: Foreign key to `Vendor.id`
- `purchase_order_id`: Foreign key to `PurchaseOrder.id`
- `invoice_number`: Vendor-provided invoice reference
- `invoice_amount`: Aggregate invoice amount evaluated in this feature slice
- `status`: One of `PENDING` or `MATCHED`
- `last_match_outcome`: One of `NONE`, `BLOCKED`, `MATCHED_WITH_WARNING`, or `MATCHED`
- `created_at`: Timestamp when the invoice was registered
- `matched_at`: Optional timestamp of the most recent successful match outcome

**Validation rules**:

- `vendor_id` must reference an existing vendor
- `purchase_order_id` must reference an existing purchase order
- `purchase_order_id` must belong to `vendor_id`
- `invoice_number` must be unique within the composite `(vendor_id, invoice_number)`
- `invoice_amount` must be greater than zero
- `status = PENDING` on creation
- `last_match_outcome = NONE` on creation
- A blocked match attempt keeps status `PENDING` while updating `last_match_outcome`
- A successful `202` or `200` match sets or preserves `status = MATCHED`
- A successful `202` match sets `last_match_outcome = MATCHED_WITH_WARNING`
- A successful `200` match sets `last_match_outcome = MATCHED`
- A previously `MATCHED` invoice may be matched again with a new idempotency key to
  refresh its outcome against newer receipt progress

### InvoiceMatchSnapshot

**Purpose**: Captures the exact result of one synchronous match evaluation for audit,
traceability, and replay semantics.

**Fields**:

- `id`: Stable match snapshot identifier
- `invoice_id`: Foreign key to `Invoice.id`
- `idempotency_key`: Caller-supplied key for the logical match request
- `outcome`: One of `BLOCKED`, `MATCHED_WITH_WARNING`, or `MATCHED`
- `invoice_amount`: Invoice amount evaluated during the attempt
- `received_value`: Receipt-backed support available at evaluation time
- `ordered_value`: Total commercial value of the linked purchase order
- `difference_amount`: Signed difference `received_value - invoice_amount`
- `shortfall_amount`: Optional uncovered amount when outcome is `BLOCKED`
- `next_action`: Enum `REQUEST_MATCH`, `WAIT_FOR_RECEIPT`, `CORRECT_INVOICE`, or `PROCEED_TO_APPROVAL` as appropriate to the outcome
- `all_lines_fully_received`: Whether every purchase-order line is fully received at evaluation time
- `warning_code`: Optional code `OPEN_RECEIPT_EXPOSURE` for partial-success outcomes
- `remaining_order_value`: Purchase-order value not yet supported by receipts at evaluation time
- `open_lines`: List of `OpenLineExposure` entries that still remain open at evaluation time
- `evaluated_at`: Timestamp of the match evaluation

**Validation rules**:

- One snapshot is written per distinct logical match request
- Replaying the same semantic request with the same idempotency key returns the same
  logical snapshot rather than creating another one
- Reusing the same idempotency key for a different semantic match request is rejected
- `difference_amount < 0` only when `outcome = BLOCKED`
- `shortfall_amount > 0` only when `outcome = BLOCKED`
- `warning_code` is populated only when `outcome = MATCHED_WITH_WARNING`
- `open_lines` is empty only when all lines are fully received

### ReceivedValueSnapshot

### ReceivedValueSnapshot

**Purpose**: Derived view of the current receipt-backed support for an invoice's
linked purchase order at the moment matching is requested.

**Fields**:

- `purchase_order_id`
- `received_value`: `sum(qty_received * unit_cost)` across PO lines
- `ordered_value`: `sum(qty_ordered * unit_cost)` across PO lines
- `difference_amount`: `received_value - invoice_amount`
- `remaining_order_value`: `ordered_value - received_value`
- `is_fully_received`: True when every PO line has `qty_received = qty_ordered`
- `open_lines`: List of line-level open exposure derived from current PO progress

**Validation rules**:

- Derived from current purchase-order line progress and unit costs
- Must never use ordered value alone as match support
- Must reflect the latest committed receipt data visible at request time

### OpenLineExposure

**Purpose**: Describes one purchase-order line that remains partially or wholly open
when a match is evaluated.

**Fields**:

- `po_line_item_id`: Identifier of the purchase-order line
- `sku`: SKU or item identifier
- `qty_remaining`: Quantity not yet received for the line
- `remaining_value`: Commercial value still open for the line

### OpenExposureWarning

**Purpose**: Non-blocking warning payload returned when the invoice is supportable but
the linked purchase order remains partially unreceived.

**Fields**:

- `code`: Stable code `OPEN_RECEIPT_EXPOSURE`
- `message`: Machine-readable descriptive text
- `exposure_amount`: Aggregate commercial value that remains open on the purchase order
- `remaining_order_value`: Unreceived commercial value still open on the purchase order
- `purchase_order_status`: Current purchase-order lifecycle state
- `open_lines`: List of `OpenLineExposure` entries

**Validation rules**:

- Emitted only when `invoice_amount <= received_value` and the purchase order is not
  fully received
- Omitted for clean `200` matches

## Relationships

- `Vendor 1 -> many Invoice`
- `PurchaseOrder 1 -> zero or one Invoice` in the broader lifecycle
- `Invoice 1 -> many InvoiceMatchSnapshot`
- `Invoice 1 -> one PurchaseOrder`
- `InvoiceMatchSnapshot many -> one Invoice`
- `ReceivedValueSnapshot` is derived from `PurchaseOrder` and `POLineItem`

## Business Invariants

- The same invoice number may exist for different vendors, but not twice for the same
  vendor
- At most one invoice may be registered against a purchase order in this feature slice
- An invoice may only register against a purchase order owned by the same vendor
- Invoice matching must evaluate against received value, not ordered value
- A hard reject match must return the exact uncovered amount and a structured next
  action
- A successful partial-receipt match returns a warning but remains a successful match
- A clean match omits the open-exposure warning
- Every match response returns signed difference, full-receipt indicator, and open-line details
- Idempotent replay must preserve the original logical outcome for the same request
- Re-evaluation after receipt progress changes requires a new idempotency key

## State Transitions

### Invoice

- `PENDING -> MATCHED`: valid when a `202` or `200` match succeeds
- `MATCHED -> MATCHED`: valid when the invoice is re-matched with a new idempotency
  key after new receipt progress and the result remains successful or becomes cleaner
- `PENDING -> PENDING`: valid when a `422` match attempt is blocked

Invalid match attempts caused by incoherent relationships, conflicting idempotency
keys, or unsupported workflow states must return stable machine-readable business
errors rather than mutate invoice state.
