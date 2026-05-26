# ADR 019: Vendor-Level Credit Alert Model

## Status

Accepted

## Context

The original assignment describes an async background task that "flags invoices" when
the vendor's total open AP exceeds the credit limit. Feature `019-vendor-credit-alert`
keeps the async requirement and the credit-limit breach rule, but the reviewed spec
requires the finance agent to retrieve any active alert through the existing vendor
exposure checkpoint before approval.

That checkpoint is vendor-oriented, and the breach itself is derived from vendor-wide
outstanding obligations across multiple invoices. A literal invoice-level flag would
duplicate records for the same vendor-wide risk condition and complicate retrieval.

## Decision

Use a vendor-level `CreditAlert` model with at most one active alert per vendor.

- The background task runs after successful invoice create or approve actions.
- When `outstanding_total_amount > credit_limit_amount`, the task upserts the current
  alert for that vendor and correlates it to the triggering invoice.
- When a later completed check finds exposure at or below the limit, any existing
  active alert for that vendor is cleared.
- The alert is surfaced through the existing vendor exposure endpoint instead of a new
  router or invoice response field.

## Consequences

### Positive

- The alert model matches the vendor-wide nature of the breach condition.
- Vendor exposure remains the single natural checkpoint for finance review.
- Alert storage is bounded to one current record per vendor.
- Create and approve responses remain unchanged and non-blocking.

### Negative

- The implementation deviates from the original invoice-level phrasing and must be
  explained to reviewers.
- Historical breach auditing is not provided in this phase.

## Alternatives Considered

### 1. Flag each triggering invoice separately

Rejected because the same vendor-wide breach could generate multiple invoice-level
records with overlapping meaning and no clearer retrieval path.

### 2. Add a dedicated alert endpoint

Rejected because the existing vendor exposure endpoint is already the intended natural
checkpoint and a new router would increase interface surface area without adding user
value.
