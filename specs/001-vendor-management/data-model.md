# Data Model: Vendor Management

## Overview

This feature models vendor eligibility as master data and AP exposure as a derived read
model computed from unpaid invoices. No vendor create or update workflow is part of
this feature; vendor records are seeded at startup.

## Entities

### Vendor

**Purpose**: Represents a supplier whose active status controls whether new obligations
may be created.

**Fields**:

- `id`: Stable vendor identifier
- `name`: Human-readable vendor name used in agent context and audit output
- `payment_terms`: Vendor payment terms such as `NET30` or `NET60`
- `is_active`: Boolean flag controlling eligibility for new obligations

**Validation rules**:

- `id` must be unique
- `name` must be non-empty
- `payment_terms` must be one of the supported terms defined for the PoC seed set
- `is_active = false` means the vendor is ineligible for new obligations

### Invoice

**Purpose**: Provides the unpaid obligation data used to derive AP exposure.

**Fields used by this feature**:

- `id`: Stable invoice identifier
- `vendor_id`: Foreign key to `Vendor.id`
- `po_id`: Reference to the related purchase order
- `invoice_number`: External vendor invoice reference
- `amount`: Invoice monetary amount
- `status`: Invoice state; unpaid invoices remain part of exposure until `PAID`

**Validation rules**:

- `vendor_id` must reference an existing vendor
- `amount` must be greater than zero
- `status` must be one of `PENDING`, `MATCHED`, `APPROVED`, or `PAID`

### VendorEligibilityResult

**Purpose**: Read model returned by the eligibility capability.

**Fields**:

- `vendor_id`
- `vendor_name`
- `is_active`
- `obligations_allowed`: Derived boolean; true only when the vendor exists and is active
- `blocking_reason_code`: Null for active vendors, otherwise a stable machine-readable code
- `blocking_reason_message`: Human-readable explanation suitable for logs

### OutstandingPaymentObligationSummary

**Purpose**: Derived AP exposure view for a single vendor.

**Fields**:

- `vendor_id`
- `vendor_name`
- `as_of_timestamp`: Time the exposure calculation was produced
- `outstanding_total_amount`: Sum of all unpaid invoices for the vendor at request time
- `open_invoice_count`: Count of unpaid invoices included in the total
- `included_invoice_statuses`: Invoice statuses included in the calculation

**Derived calculation**:

- Include invoices where `status != PAID`
- Exclude invoices where `status = PAID`
- `outstanding_total_amount = sum(invoice.amount for all included invoices)`
- `open_invoice_count = count(all included invoices)`

## Relationships

- `Vendor 1 -> many Invoice`
- `Vendor 1 -> 1 VendorEligibilityResult` (derived per lookup)
- `Vendor 1 -> 1 OutstandingPaymentObligationSummary` (derived per lookup)

## Business Invariants

- A vendor that does not exist returns `VENDOR_NOT_FOUND`
- A vendor that exists but is inactive returns `is_active = false` and
  `obligations_allowed = false`
- Downstream mutating operations must reject inactive vendors with the shared stable
  error code `VENDOR_INACTIVE`
- Exposure lookup for a valid vendor with no unpaid invoices returns a zero-value
  summary, not an error
- Temporary persistence or retrieval failures must produce a retryable infrastructure
  error distinct from permanent business rejections

## State Considerations

- `Vendor.is_active` is the authoritative source for eligibility at lookup time
- Invoice states relevant to this feature are `PENDING`, `MATCHED`, `APPROVED`, and
  `PAID`; only `PAID` exits the exposure calculation set
- If vendor status changes after a prior eligibility check, downstream mutating flows
  must re-evaluate status at execution time rather than relying on cached caller state
