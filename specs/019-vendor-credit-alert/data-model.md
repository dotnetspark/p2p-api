# Data Model: Vendor Credit Alert

## Overview

This feature adds a durable `CreditCheckRecord` that is created before a background
credit evaluation runs, plus a vendor-scoped `CreditAlert` that represents the most
recent active breach. The credit check gives agents a deterministic query handle,
while vendor exposure remains the natural place to view full escalation context.

## Entities

### CreditCheckRecord

**Purpose**: Represents one scheduled background credit evaluation triggered by a
successful logical invoice create or approve action.

**Fields**:

- `id`: UUID credit-check identifier returned to the caller immediately
- `vendor_id`: Foreign key to `Vendor.id`
- `triggering_invoice_id`: Foreign key to `Invoice.id`
- `triggering_action`: Enum scoped to `CREATE` or `APPROVE`
- `status`: Enum scoped to `PENDING` or `COMPLETED`
- `breached`: Nullable boolean. `null` while pending, then `true` or `false` when completed
- `alert_id`: Nullable foreign key to `CreditAlert.id`
- `correlation_id`: Correlation identifier captured from the triggering request
- `idempotency_key`: Idempotency key associated with the logical triggering request
- `created_at`: Timestamp when the pending record is written
- `completed_at`: Nullable timestamp set when the task finishes

**Validation rules**:

- The record is created before the background task is scheduled
- `status = PENDING` requires `breached = null`, `alert_id = null`, and `completed_at = null`
- `status = COMPLETED` requires `breached` to be non-null and `completed_at` to be populated
- `alert_id` is populated only when `breached = true`
- Idempotent replay of the same logical success returns the same `id`
- Replayed requests must not create a second pending record or schedule duplicate work

### CreditAlert

**Purpose**: Represents the most recent active vendor credit-limit breach detected by
the background exposure check.

**Fields**:

- `id`: Stable alert identifier
- `vendor_id`: Foreign key to `Vendor.id`
- `credit_check_id`: Foreign key to `CreditCheckRecord.id`
- `triggering_invoice_id`: Foreign key to `Invoice.id`
- `outstanding_amount`: Vendor outstanding AP total at check time
- `credit_limit`: Vendor credit limit at check time
- `percentage_consumed`: Decimal percentage derived from `outstanding_amount / credit_limit * 100`
- `breached_at`: Timestamp when the background check confirmed the breach
- `status`: Current alert lifecycle value, scoped to `ACTIVE` for this feature

**Validation rules**:

- At most one `ACTIVE` alert exists per vendor
- `outstanding_amount` must be strictly greater than `credit_limit`
- `credit_check_id` must reference the completed breached check that created or replaced the alert
- `triggering_invoice_id` must identify the invoice action that caused the check to run
- `percentage_consumed` must be stored with enough precision for machine-readable escalation context
- A later breach for the same vendor replaces the previous active alert contents
- A later non-breach check clears any existing active alert for that vendor

### Outstanding Payment Obligation Summary

**Purpose**: Represents the vendor exposure total used by both the existing exposure
endpoint and the new breach check.

**Fields**:

- `vendor_id`
- `outstanding_total_amount`
- `open_invoice_count`
- `included_invoice_statuses`
- `as_of_timestamp`

**Validation rules**:

- `outstanding_total_amount` is the sum of invoice amounts for statuses `PENDING`,
  `MATCHED`, and `APPROVED`
- `PAID` invoices are excluded from the total and count
- The same aggregate definition is used for endpoint reporting and breach evaluation

### Invoice Response Extension

**Purpose**: Extends successful invoice create and approve responses with a
deterministic credit-check identifier while leaving existing business fields intact.

**Fields**:

- Existing response body fields from invoice create or approve
- `credit_check_id`

**Validation rules**:

- Existing business response fields remain unchanged by this feature
- `credit_check_id` is present for each successful logical create or approve response
- The agent queries `GET /credit-checks/{credit_check_id}` using the returned identifier

### Vendor Exposure Response Extension

**Purpose**: Extends the existing vendor exposure response with the current active
credit alert when one exists.

**Fields**:

- Existing exposure summary fields from feature `001`
- Optional `active_credit_alert` object containing:
  - `alert_id`
  - `vendor_id`
  - `credit_check_id`
  - `triggering_invoice_id`
  - `outstanding_amount`
  - `credit_limit`
  - `percentage_consumed`
  - `breached_at`
  - `advisory_only`

**Validation rules**:

- `active_credit_alert` is omitted entirely when no active alert exists
- When present, it reflects the current active vendor-level breach only
- The payload provides escalation context but does not prescribe a machine action

## Relationships

- `Vendor 1 -> many CreditCheckRecord`
- `Vendor 1 -> 0..1 CreditAlert`
- `Vendor 1 -> many Invoice`
- `Invoice 1 -> many CreditCheckRecord`
- `CreditCheckRecord 1 -> 0..1 CreditAlert`

## State Transitions

### CreditCheckRecord

- `PENDING -> COMPLETED (breached = false)`: the background task finishes and finds `outstanding_total_amount <= credit_limit`
- `PENDING -> COMPLETED (breached = true)`: the background task finishes and finds `outstanding_total_amount > credit_limit`, then links the resulting alert

### CreditAlert

- `ABSENT -> ACTIVE`: a completed credit check finds `outstanding_total_amount > credit_limit`
- `ACTIVE -> ACTIVE`: a later breached check for the same vendor replaces the existing active alert with newer values
- `ACTIVE -> ABSENT`: a later completed credit check finds `outstanding_total_amount <= credit_limit`

## Derived Rules

- Successful create and approve responses return a top-level `credit_check_id`, not alert data
- Background checks run only after successful parent actions commit
- Idempotent replay of the parent action does not create a second background dispatch
- Vendor exposure remains equivalent to the prior feature when no active alert exists
- The credit-check query endpoint returns workflow state only: `status`, `breached`, and `alert_id`
