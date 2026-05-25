# Research: Invoice Approval and Payment

## Decision: Reuse the existing Python 3.14 FastAPI service and SQLite stack

**Rationale**: The repository already standardizes on Python 3.14, FastAPI,
SQLAlchemy 2.x, and SQLite for the earlier purchase-order and invoice workflows.
Continuing with the same stack keeps the feature aligned with the constitution's
simplicity rule and avoids introducing a second accounting service for a tightly
adjacent workflow step.

**Alternatives considered**:

- A separate accounting microservice: would isolate ledger concerns, but it adds
  distributed workflow complexity and weakens traceability for this interview-scale
  slice.
- A different persistence technology for GL entries: unnecessary while current scale
  and local validation needs fit the existing SQLite-backed service.

## Decision: Treat invoice approval as generating exactly two balancing GL entries

**Rationale**: The original assignment explicitly requires approval of a matched
invoice to generate two accounting records: one for the payable obligation and one for
the expense. The feature therefore treats approval as a deterministic accounting
operation that always emits exactly two entries which balance for the invoice amount.

**Alternatives considered**:

- Allow a variable number of entries per approval: more flexible for full accounting
  scenarios, but it weakens the machine-observable contract required by the assignment.
- Post entries asynchronously later: reduces request latency, but it complicates the
  agent's understanding of whether approval actually succeeded.

## Decision: Derive the expense account from vendor category using a hardcoded account map with fallback

**Rationale**: The user explicitly constrained expense classification to a hardcoded
vendor-category map and required that approval must never fail because a category is
missing or unmapped. The design therefore uses a deterministic mapping rule with an
`UNCLASSIFIED_EXPENSE` catch-all account so the approval workflow remains robust.

**Alternatives considered**:

- Fail approval when vendor category is missing: would produce stricter accounting
  hygiene, but it violates the requested workflow resilience.
- Add a configurable external account-mapping service: more extensible, but beyond the
  current scope and unnecessary for the PoC.

## Decision: Keep payment as an explicit API step that transitions APPROVED to PAID and triggers PO closure

**Rationale**: The original assignment explicitly requires approval and GL posting.
The user additionally requested payment completion and automatic purchase-order
closure. Modeling payment as a separate explicit step preserves lifecycle determinism:
`MATCHED -> APPROVED -> PAID`, with the linked purchase order closing only after
successful payment.

**Alternatives considered**:

- Mark invoices paid during approval: simpler, but it collapses two business steps and
  violates the requested no-skipped-steps rule.
- Leave purchase-order closure manual after payment: weaker workflow completion and
  lower agent autonomy.

## Decision: Reuse the shared idempotency registry for approval and payment

**Rationale**: Earlier features already established a deterministic idempotency pattern
based on operation name, request fingerprint, and stable resource replay. Reusing that
pattern for approval and payment preserves safe retries without inventing feature-
specific duplicate suppression logic.

**Alternatives considered**:

- Per-invoice status flags only: too weak to distinguish a legitimate retry from a
  conflicting semantic request.
- No idempotency for approval or payment: unsafe for an agent-first API where retries
  are expected.

## Decision: Treat payment as business completion rather than bank integration

**Rationale**: The feature goal is to complete the invoice and purchase-order
lifecycle inside the PoC API. Modeling payment as business completion, rather than a
real treasury integration, keeps the scope bounded while still allowing the books and
operational state to advance coherently.

**Alternatives considered**:

- Integrate with an external payment rail: more realistic, but far outside the
  interview feature slice.
- Omit payment entirely: simpler, but it would fail the user's requested lifecycle
  completion.
