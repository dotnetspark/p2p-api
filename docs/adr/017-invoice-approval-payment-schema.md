# ADR 017: Invoice Approval, Payment, and GL Entry Schema

## Status

Accepted

## Context

Feature `017-invoice-approval-payment` extends the existing invoice-matching flow
into approval and payment. The current schema supports invoice creation and match
snapshots, but it does not yet persist approval timestamps, payment timestamps, or
the two ledger rows created by approval.

The project constitution requires schema-affecting implementation work to be backed
by a feature plan, regenerated data model, and an ADR that explains the rationale and
scope of the change.

The original assignment's GL example also reverses the usual accounting direction by
saying approval should debit `AP Control` and credit `Expense`. The repository treats
that as a prompt defect rather than a business rule because the constitution makes
financial correctness non-negotiable.

## Decision

The implementation will extend the current schema in the following way:

1. Add `approved_at` and `paid_at` columns to the `invoices` table.
2. Add a new `gl_entries` table keyed by `invoice_id` with `account_code`, `debit`,
   `credit`, and `posted_at` fields.
3. Extend invoice domain status handling from `PENDING/MATCHED` to
   `PENDING/MATCHED/APPROVED/PAID`.
4. Keep vendor classification out of the vendor schema for this slice. Approval will
   use a hardcoded business rule to derive a category from current vendor master data
   when possible, and fall back to `UNCLASSIFIED_EXPENSE` when category data is absent
   or unmapped.

## Consequences

### Positive

- Approval can persist exactly two GL rows and replay them deterministically.
- Approval now uses standard accrual accounting direction by debiting expense and
  crediting `AP_CONTROL`.
- Payment can persist a terminal invoice state and support PO closure.
- The feature remains within the current FastAPI and SQLAlchemy architecture.
- Vendor schema does not need to widen during this slice.

### Negative

- Category-to-account derivation is intentionally heuristic and repo-local for this
  PoC rather than backed by a full accounting master-data model.
- The new `gl_entries` table introduces another persisted entity that must be kept in
  sync with invoice approval rules.

## Alternatives Considered

### 1. Add a vendor category column before implementing approval

Rejected for this slice because it would widen the vendor schema and earlier feature
artifacts beyond what is necessary to complete the approval and payment workflow.

### 2. Store approval GL rows inside invoice snapshots instead of a dedicated table

Rejected because ledger rows are first-class accounting records and should be stored
explicitly rather than encoded into a snapshot payload.

### 3. Follow the prompt's GL direction literally

Rejected because debiting accounts payable control and crediting expense would invert
the accounting meaning of invoice recognition. The repository keeps the prompt as a
historical source document but corrects the implementation and owned specs to standard
accounting.
