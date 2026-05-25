# Feature Specification: Invoice Approval and Payment

**Feature Branch**: `feat/017-invoice-approval-payment`

**Created**: 2026-05-24

**Status**: Draft

**Input**: User description: "A finance agent needs to approve a matched invoice and have the corresponding accounting entries generated automatically — one recording the payment obligation and one recording the expense categorised by vendor type — so the organisation's books reflect the liability without manual journal entry. The agent must also be able to mark an approved invoice as paid which automatically closes the linked purchase order. No step in this lifecycle can be skipped — an invoice must be matched before it can be approved and approved before it can be paid."

## Context

This feature extends the current invoice workflow after 3-way matching. It allows a
finance agent to move a matched invoice into an approved accounting state with
machine-generated journal records, and then complete the invoice lifecycle by marking
it paid and closing the linked purchase order.

The approval and GL-posting portion is directly aligned with the original assignment.
The payment-and-close portion is the next workflow step requested for this repository
so the end-to-end purchase-to-pay lifecycle can be completed without manual state
changes.

This feature depends on the existing invoice-matching slice for matched invoice state,
on vendor-management data for vendor classification, and on the purchase-order
lifecycle for purchase-order closure.

## User Scenarios & Testing _(mandatory)_

### User Story 1 - Approve Matched Invoice (Priority: P1)

As a finance agent, I want to approve a matched invoice and have the accounting
entries created automatically so the organisation records both the payable obligation
and the expense without manual journal entry.

**Why this priority**: The original assignment explicitly requires approval of a
matched invoice and automatic GL posting. Without this step, the accounting impact of
procurement cannot be recorded.

**Independent Test**: Can be fully tested by approving a matched invoice and
verifying that the invoice moves to an approved state and exactly two balancing
accounting entries are created with the expected business meaning.

**Acceptance Scenarios**:

1. **Given** an invoice is already in a matched state, **When** the finance agent
   requests approval, **Then** the system marks the invoice approved and records the
   payable obligation automatically.
2. **Given** an invoice is already in a matched state, **When** the finance agent
   requests approval, **Then** the system records the corresponding expense
   automatically using the vendor's category or type.
3. **Given** an invoice is not in a matched state, **When** the finance agent
   requests approval, **Then** the system rejects the request and leaves both the
   invoice state and accounting records unchanged.
4. **Given** an approval request is retried with the same idempotency key and the
   same semantic request, **When** the agent repeats the request, **Then** the system
   returns the original logical outcome without creating duplicate accounting entries.

---

### User Story 2 - Pay Approved Invoice and Close Purchase Order (Priority: P2)

As a finance agent, I want to mark an approved invoice as paid and automatically close
its linked purchase order so the financial and operational lifecycle completes without
manual reconciliation.

**Why this priority**: Once approval is complete, the next valuable step is to finish
payment and bring the linked purchase order to a financially complete closed state.

**Independent Test**: Can be fully tested by marking an approved invoice paid and
verifying that the invoice moves to paid state, the linked purchase order closes, and
invalid pre-approval payment attempts are rejected.

**Acceptance Scenarios**:

1. **Given** an invoice is already approved, **When** the finance agent marks it as
   paid, **Then** the system records the invoice as paid.
2. **Given** an invoice is already approved and linked to an open purchase order,
   **When** the finance agent marks it as paid, **Then** the system closes the linked
   purchase order automatically.
3. **Given** an invoice is not yet approved, **When** the finance agent attempts to
   mark it paid, **Then** the system rejects the request and leaves both invoice and
   purchase-order states unchanged.
4. **Given** a payment request is retried with the same idempotency key and the same
   semantic request, **When** the agent repeats the request, **Then** the system
   returns the original logical outcome without duplicating the state transition.

### Edge Cases

- What happens when the same approval request is retried after the invoice was already
  approved successfully?
- How does the system respond when an approval or payment request is valid in general
  but the invoice is currently in the wrong lifecycle state?
- How does the system behave when the linked purchase order cannot be closed after the
  invoice is marked paid?
- What happens when vendor category or type information needed for expense
  classification is missing or unusable at approval time?

## Requirements _(mandatory)_

### Functional Requirements

- **FR-001**: The system MUST allow a finance agent to approve an invoice only when
  that invoice is already in a matched state.
- **FR-002**: The system MUST reject approval attempts for invoices that are not in a
  matched state.
- **FR-003**: When an invoice is approved, the system MUST transition the invoice to
  an approved state.
- **FR-004**: When an invoice is approved, the system MUST generate one accounting
  entry representing the payable obligation.
- **FR-005**: When an invoice is approved, the system MUST generate one accounting
  entry representing the expense.
- **FR-006**: The system MUST classify the expense entry using vendor type or vendor
  category business rules.
- **FR-007**: The system MUST ensure the accounting entries created by approval are
  financially balanced as one payable obligation and one expense record for the same
  approved invoice.
- **FR-008**: The system MUST allow a finance agent to mark an invoice paid only when
  that invoice is already approved.
- **FR-009**: The system MUST reject payment attempts for invoices that are not in an
  approved state.
- **FR-010**: When an invoice is marked paid, the system MUST transition the invoice
  to a paid state.
- **FR-011**: When an approved invoice is marked paid, the system MUST close the
  linked purchase order automatically.
- **FR-012**: The system MUST prevent lifecycle steps from being skipped so an invoice
  cannot be approved before matching and cannot be paid before approval.
- **FR-013**: The system MUST preserve idempotent behavior for approval and payment
  requests so identical retries do not create duplicate side effects.
- **FR-014**: The system MUST reject reuse of an idempotency key for a different
  semantic approval or payment request with a stable machine-readable business error.
- **FR-015**: The system MUST distinguish permanent business failures from retryable
  infrastructure failures for approval and payment workflows.
- **FR-016**: The system MUST leave invoice, purchase-order, and accounting-record
  state unchanged when approval or payment is rejected.
- **FR-017**: The system MUST preserve traceability between invoice lifecycle
  transitions and the accounting entries created for that invoice.

### API Contract & Recovery Requirements _(mandatory for APIs)_

- The invoice-approval capability must define the exact request and response shape for
  approving a matched invoice, including invoice identifier, resulting lifecycle
  state, generated accounting-entry identifiers, and correlation data.
- The invoice-payment capability must define the exact request and response shape for
  marking an approved invoice paid, including invoice identifier, resulting paid
  state, linked purchase-order closure result, and correlation data.
- Approval failures must clearly distinguish invalid invoice state, missing vendor
  category or expense classification context, and retryable infrastructure failure.
- Payment failures must clearly distinguish invalid invoice state, purchase-order
  closure failure, and retryable infrastructure failure.
- Approval and payment operations must define idempotency expectations for identical
  retries and for conflicting reuse of the same idempotency key.
- Responses must carry the identifiers and telemetry fields needed to correlate
  invoice approval, accounting-entry creation, payment completion, purchase-order
  closure, and retry handling.

### Key Entities _(include if feature involves data)_

- **Invoice Approval Result**: A machine-readable outcome describing whether a matched
  invoice was approved, which accounting entries were created, and what lifecycle
  state the invoice now occupies.
- **GL Entry**: An accounting record generated from invoice approval that represents
  either the payable obligation or the expense for the approved invoice.
- **Invoice Payment Result**: A machine-readable outcome describing whether an
  approved invoice was marked paid and whether the linked purchase order was closed.
- **Vendor Category Rule**: The business classification used to determine which
  expense category applies to an approved invoice.

## Success Criteria _(mandatory)_

### Measurable Outcomes

- **SC-001**: In representative validation scenarios, 100% of approval attempts for
  matched invoices create exactly two accounting entries with no manual journal entry
  required.
- **SC-002**: In representative validation scenarios, 100% of approval attempts for
  invoices that are not matched are rejected before any accounting entries are created.
- **SC-003**: In representative validation scenarios, 100% of payment attempts for
  approved invoices result in both invoice payment completion and linked
  purchase-order closure.
- **SC-004**: In representative validation scenarios, 100% of payment attempts for
  invoices that are not approved are rejected before any lifecycle state changes occur.
- **SC-005**: Finance agents can complete approval and payment handling for valid
  invoices without manual accounting entry creation in at least 95% of requests.
- **SC-006**: In representative retry scenarios, 100% of duplicate approval and
  payment requests with the same idempotency key replay safely without duplicating
  lifecycle transitions or accounting records.

## Assumptions

- Vendor category or vendor type information needed for expense classification is
  already available through existing vendor master data or a maintained business rule.
- The current repository constraint of one invoice per purchase order remains in force
  for this slice, so marking the approved invoice paid is sufficient to close the
  linked purchase order.
- Marking an invoice paid in this slice records business completion of payment, not
  integration with an external banking or treasury platform.
- Reversals, partial payments, and manual accounting overrides are outside the scope
  of this feature slice.
