# Research: Invoice Matching

## Decision: Reuse the existing Python 3.14 FastAPI service and SQLite stack

**Rationale**: The repository already standardizes on Python 3.14, FastAPI,
SQLAlchemy 2.x, and SQLite for adjacent P2P workflows. Reusing that stack keeps the
feature aligned with the constitution's simplicity rule and avoids introducing a
second runtime or persistence model for a directly adjacent finance workflow.

**Alternatives considered**:

- TypeScript or a separate invoice service: viable in isolation, but it would add
  integration and deployment complexity without improving the caller-visible PoC
  contract.
- New database technology for invoice history: unnecessary while current workload and
  durability expectations fit the existing SQLite-backed service.

## Decision: Treat duplicate invoice registration as a composite business rule on `(vendor_id, invoice_number)`

**Rationale**: The user explicitly constrained duplicate detection to vendor and
invoice number together. This lets different vendors reuse the same external invoice
number while preventing ambiguous duplicate obligations for the same vendor.

**Alternatives considered**:

- Global uniqueness on `invoice_number`: too restrictive because vendor-issued invoice
  numbers are not globally coordinated.
- Uniqueness on `(purchase_order_id, invoice_number)`: weaker than requested and would
  allow the same vendor invoice to be registered twice across different orders.

## Decision: Start invoices in `PENDING` and make registration responses point the agent to matching next

**Rationale**: The original assignment draft requires invoice creation to establish a
tracked payable obligation without implying that matching or approval has already
occurred. Returning `PENDING` plus an explicit next action keeps the control flow
machine-actionable while staying aligned with the repo's existing invoice status
vocabulary.

**Alternatives considered**:

- Start invoices in `REGISTERED`: acceptable internally, but it drifts from the
  earlier assignment wording and from the repository's current invoice status usage.
- Auto-match on create: outside the intended workflow boundary because the finance
  agent triggers matching explicitly.

## Decision: Evaluate matching from receipt-backed value, not ordered value

**Rationale**: Financial correctness requires using only goods actually received as
support for invoice payment. The support basis is the current received value derived
from purchase-order line progress: `sum(qty_received * unit_cost)` across the linked
purchase order.

**Alternatives considered**:

- Ordered-value matching: simpler, but it would allow payment before delivery and
  violates the feature goal.
- Line-by-line invoice allocation in this slice: more precise, but outside the scope
  of this feature because the specification treats invoice amount as one aggregate
  value.

## Decision: Constrain the current slice to one invoice per purchase order, while documenting multiple invoices per PO as the production direction

**Rationale**: The original assignment says an invoice is linked to a purchase order,
but it does not explicitly require one invoice per purchase order. For this interview
slice, constraining the implementation to one invoice per PO keeps the data model,
matching semantics, and recovery logic small enough to ship cleanly. That is a PoC
tradeoff, not a statement about ideal production ERP behavior.

**Alternatives considered**:

- Support multiple invoices per PO immediately: closer to production ERP practice,
  but it would require cumulative invoiced-value or quantity controls, more nuanced
  approval rules, and likely invoice-line modeling that would materially expand the
  slice.
- Leave the rule undocumented: simpler in the short term, but it would wrongly imply
  that the current one-invoice-per-PO implementation was inherited directly from the
  original assignment rather than chosen for scoped delivery.

## Decision: Use three explicit synchronous match outcomes with HTTP `422`, `202`, and `200`

**Rationale**: The user explicitly required three distinct outcomes. The contract
therefore treats match evaluation as a synchronous decision with three caller-visible
results: blocked (`422`) when receipt-backed value is insufficient, matched with
warning (`202`) when the invoice is supportable but the purchase order remains
partially open, and clean matched (`200`) when the order is fully received and the
invoice amount is supportable.

**Alternatives considered**:

- Single `200` response with an internal outcome enum: simpler HTTP surface, but it
  discards the explicit transport-level distinction the user requested.
- `409` for blocked matches: plausible for business conflicts, but rejected because
  the user explicitly chose `422` for hard reject match outcomes.

## Decision: Keep matching idempotent per request and require a new idempotency key for re-evaluation after new receipts

**Rationale**: Identical retries must replay the original logical outcome for safe
agent recovery. That means a retried match request with the same idempotency key must
return the original `422`, `202`, or `200` result even if additional receipts arrived
afterward. To intentionally re-evaluate against newer receipt progress, the caller
issues a new match request with a fresh idempotency key.

**Alternatives considered**:

- Recompute the outcome on every retry even with the same idempotency key: would make
  retry behavior nondeterministic and break safe replay guarantees.
- Forbid matching an already matched invoice: incompatible with the user requirement
  that matched invoices may be re-matched after additional receipts arrive.

## Decision: Record structured match snapshots so every evaluation is traceable

**Rationale**: The constitution requires inspectability across workflow steps.
Persisting a lightweight snapshot per match attempt captures the invoice amount,
received-value basis, shortfall, next action, and warning details used for the agent
decision while keeping matching synchronous.

**Alternatives considered**:

- Store only the latest invoice state and discard prior evaluations: simpler, but it
  weakens traceability and makes rematch reasoning harder.
- Push match history into logs only: insufficient because the workflow needs
  domain-level traceability, not just operational logging.

## Decision: Include line-level open exposure details and signed value difference in every match response

**Rationale**: The original assignment draft requires every match outcome to report
invoice amount, received value, the difference, whether all lines are fully received,
and the open lines list. Exposing those fields consistently keeps the warning and
clean outcomes distinguishable without forcing the agent to reconstruct line state
from separate purchase-order queries.

**Alternatives considered**:

- Return only summary values and hide line details behind a follow-up query: weaker
  agent ergonomics and inconsistent with the earlier draft.
- Return open-line details only for warning outcomes: simpler, but it makes the match
  payload shape vary more than needed and weakens machine branching consistency.

## Decision: Derive next action from whether remaining purchase-order value can still cover the shortfall

**Rationale**: Blocked matches must tell the agent whether to wait for additional
goods receipt or correct the invoice. If the invoice shortfall is less than or equal
to the order's remaining unreceived value, the next action is `WAIT_FOR_RECEIPT`.
If the invoice amount exceeds even the total order value, the next action is
`CORRECT_INVOICE` because future receipts cannot legitimately cure the mismatch.

**Alternatives considered**:

- Always tell the agent to wait for receipt: incorrect when the invoice exceeds the
  total commercial obligation.
- Always tell the agent to correct the invoice: too strict when more goods can still
  arrive and legitimately support the invoice.

## Decision: Treat exact equality as non-overbilling, but still warn when open lines remain

**Rationale**: Equality between invoice amount and current received value is not a
blocking mismatch. However, the original assignment also requires a warning whenever
the purchase order remains partially received. The outcome therefore depends on both
value support and receipt completeness: equality is warning if open lines remain and
clean only when all lines are fully received.

**Alternatives considered**:

- Always treat equality as clean: conflicts with the explicit partial-receipt warning
  requirement when open lines still exist.
- Always treat equality as warning: too strict when the purchase order is already
  fully received.
