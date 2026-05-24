# Research: Purchase Order Lifecycle

## Decision: Reuse the existing Python 3.14 FastAPI service and SQLite stack

**Rationale**: The repository already contains a working FastAPI, SQLAlchemy 2.x,
and SQLite service for vendor management. Reusing that stack keeps the feature
aligned with the constitution's simplicity rule and avoids introducing a second
runtime or persistence model for a directly adjacent workflow.

**Alternatives considered**:

- TypeScript/Express: viable for the original assignment, but unnecessary once the
  repo has already standardized on Python and FastAPI.
- Separate purchase-order microservice: would add operational complexity without
  improving the caller-visible contract for this PoC.

## Decision: Model receipt progress with explicit GoodsReceipt events plus additive per-line cumulative progress

**Rationale**: The assignment requires both multi-receipt history and full order-state
queries with line-level progress. The design therefore keeps append-only goods receipt
events for auditability while exposing cumulative ordered, received, and remaining
quantities per purchase-order line for agent decisions. Each accepted receipt adds to
the existing `qty_received` total for the affected line and never overwrites prior
receipt progress.

**Alternatives considered**:

- Replace `qty_received` on each receipt with the latest delivery quantity: simpler
  implementation, but incorrect for partial-receipt accumulation and incompatible
  with the business rule that receipt totals span multiple events.
- Store only raw receipt events and derive all progress at read time with no line
  progress fields: workable, but makes progress validation and order-state reads more
  complex for minimal PoC benefit.

## Decision: Keep purchase-order states aligned to DRAFT, SUBMITTED, and RECEIVED, with CLOSED reserved for GL Posting invoice-payment completion

**Rationale**: The original assignment names `DRAFT`, `SUBMITTED`, `RECEIVED`, and
`CLOSED`. This feature implements the purchase-order slice only, so it needs explicit
state meaning for creation, submission, and full receipt while acknowledging that
`CLOSED` is triggered later by invoice payment in the GL Posting feature, not by
receipt completion in this slice.

**Alternatives considered**:

- Introduce a persisted `PARTIALLY_RECEIVED` state: clearer at a glance, but it is not
  required by the assignment and can be represented through line progress while the
  order remains `SUBMITTED`.
- Omit `CLOSED` entirely from planning: simpler now, but would weaken continuity with
  the broader P2P lifecycle.

## Decision: Preserve a one-invoice-per-purchase-order boundary without implementing invoice behavior in this feature

**Rationale**: The broader P2P flow allows at most one invoice for a given purchase
order. Planning should therefore keep the purchase-order model compatible with a
future zero-or-one invoice relationship while avoiding premature invoice creation,
matching, or payment logic in this feature.

**Alternatives considered**:

- Ignore invoice cardinality until invoice implementation begins: simpler now, but
  risks designing purchase-order contracts and persistence in a way that makes the
  later one-invoice constraint awkward or inconsistent.
- Add invoice creation or closure logic now: outside the scope of this purchase-order
  lifecycle slice and would blur the boundary with later features.

## Decision: Require idempotency keys on mutating order and receipt operations

**Rationale**: The constitution prioritizes machine-first recovery semantics. Agents
may retry create, submit, and receive requests when they encounter transient failures,
so the external contract should define safe retry behavior rather than assuming human
judgment or perfect network conditions.

**Alternatives considered**:

- Rely on client-side retry discipline only: too fragile for an agent-first API.
- Make only goods receipt idempotent: insufficient because duplicate draft creation or
  duplicate submission would also break workflow determinism.

## Decision: Return machine-readable business errors for invalid workflow transitions and over-receipt

**Rationale**: The API must tell an agent whether to stop, correct input, or retry.
Stable business codes for vendor eligibility failure, invalid order state, and
over-receipt keep recovery behavior explicit while reserving retryable errors for
infrastructure failures.

**Alternatives considered**:

- Generic validation errors only: too weak for autonomous decision-making.
- Exception text as the only signal: violates the machine-first and contract-clarity
  requirements.
