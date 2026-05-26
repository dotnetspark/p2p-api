# Feature Specification: Purchase Order Lifecycle

**Feature Branch**: `feat/004-po-lifecycle`

**Created**: 2026-05-23

**Status**: Completed

**Input**: User description: "A procurement agent needs to create a purchase order against an active vendor specifying what goods are needed and at what price, submit it for fulfilment, and record goods as they arrive including partial deliveries across multiple receipts. The agent must be able to query the full state of an order including per-line receipt progress to decide whether conditions are right to proceed with invoicing. An order that has never been submitted cannot receive goods. Cumulative quantities received across all deliveries cannot exceed what was ordered."

## Context

This feature covers the purchase-order lifecycle portion of the original P2P
assignment. It defines what an agent must be able to do to create an order,
transition it into fulfilment, record receipts across multiple deliveries, and query
enough order state to decide whether later invoicing steps may proceed.

It depends on the existing vendor-management capability so purchase-order creation
can validate that the target vendor is active before a new order is created.

## Actors

- **Procurement Agent**: Creates draft purchase orders, submits them for fulfilment,
  and queries order state to decide whether downstream invoicing should proceed.
- **Warehouse Agent**: Records goods receipts, including partial deliveries across
  multiple receipt events.

## User Scenarios & Testing _(mandatory)_

### User Story 1 - Create Draft Purchase Orders (Priority: P1)

As a procurement agent, I want to create a draft purchase order for an active vendor
with the required line items, quantities, and agreed prices so that the procurement
process can begin from a valid commercial commitment.

**Why this priority**: Every later fulfilment, receipt, and invoicing step depends on
the existence of a valid purchase order.

**Independent Test**: Can be fully tested by creating a purchase order for an active
vendor with one or more lines and verifying that the order begins in a draft state
that is not yet eligible for goods receipt.

**Acceptance Scenarios**:

1. **Given** an active vendor and a set of requested goods with quantities and unit
   prices, **When** the agent creates a purchase order, **Then** the system stores a
   new order in a draft state with all requested lines intact.
2. **Given** a vendor that is inactive, **When** the agent attempts to create a
   purchase order for that vendor, **Then** the system rejects the request with a
   structured business error and does not create the order.
3. **Given** a purchase order request, **When** the line items are missing or contain
   non-positive quantity or unit-price values, **Then** the system rejects the draft
   creation request and explains the invalid commercial input.

---

### User Story 2 - Submit Draft Purchase Orders (Priority: P1)

As a procurement agent, I want to submit a draft purchase order for fulfilment so
that it enters the fulfilment process and becomes eligible for goods receipt.

**Why this priority**: Receipt recording must not begin until the order has been
formally committed for supplier fulfilment.

**Independent Test**: Can be fully tested by submitting a draft purchase order and
verifying that the state transitions to submitted, while attempts to submit an order
in any other state are rejected.

**Acceptance Scenarios**:

1. **Given** a purchase order in draft state, **When** the agent submits it for
   fulfilment, **Then** the system transitions the order into a submitted state.
2. **Given** a purchase order in any non-draft state, **When** the agent attempts to
   submit it again, **Then** the system rejects the request and identifies the current
   state and the required state for submission.

---

### User Story 3 - Record Partial Goods Receipts (Priority: P1)

As a warehouse agent, I want to record goods receipts across one or more delivery
events so that the system reflects what has physically arrived without allowing
over-receipt or invalid receiving against an unsubmitted order.

**Why this priority**: Receipt tracking is the financial control that determines
whether future invoice processing can safely proceed.

**Independent Test**: Can be fully tested by receiving part of one purchase order
line in one receipt, receiving the remainder in a later receipt, and confirming that
the cumulative received quantity never exceeds what was ordered.

**Acceptance Scenarios**:

1. **Given** a submitted purchase order with outstanding quantities, **When** the
   agent records a partial goods receipt, **Then** the system updates cumulative
   received quantities per line and keeps remaining quantities available for future
   receipts.
2. **Given** a purchase order that has never been submitted, **When** the agent
   attempts to record a goods receipt, **Then** the system rejects the receipt and no
   receipt record is created.
3. **Given** prior receipts already exist for an order line, **When** the agent tries
   to record quantities that would push the cumulative received amount above the
   ordered quantity, **Then** the system rejects the over-receipt and preserves the
   previously recorded receipt totals.

---

### User Story 4 - Query Order State And Receipt Progress (Priority: P2)

As a procurement agent, I want to retrieve the full state of a purchase order,
including per-line receipt progress, so that I can decide whether the order is ready
for invoicing or whether more fulfilment activity is still pending.

**Why this priority**: The agent cannot make reliable invoicing decisions without a
single machine-readable view of order status and cumulative receipt progress.

**Independent Test**: Can be fully tested by retrieving an order after multiple
partial receipts and verifying that the response reports both the overall order state
and the ordered, received, and remaining quantities for each line.

**Acceptance Scenarios**:

1. **Given** a purchase order with no receipts yet, **When** the agent queries the
   order, **Then** the system returns the current order state and indicates zero
   received quantity on every line.
2. **Given** a purchase order with multiple receipts across one or more lines,
   **When** the agent queries the order, **Then** the system returns cumulative
   per-line receipt progress, receipt history, and enough summary context to
   determine whether the order is still awaiting fulfilment, partially received, or
   fully received.

## Order Lifecycle Meaning

- **DRAFT**: The order exists but has not been submitted for fulfilment.
- **SUBMITTED**: The order has been submitted and may now receive goods. Partial
  receipts may occur while the order remains in this state.
- **RECEIVED**: All order lines have reached their full ordered quantity across all
  accepted goods receipts.
- **CLOSED**: A later feature may move the order into a closed state after downstream
  invoice and payment activity is complete.

This feature covers creation, submission, receipt accumulation, and order-state
visibility. It does not complete the later closure step.

### Edge Cases

- What happens when the same submission or goods-receipt request is retried with the
  same idempotency key after the original request already succeeded?
- How does the system respond when a goods receipt is requested for an order state
  that exists but is not yet eligible for receiving?
- How does the system signal a temporary persistence failure differently from a
  permanent business rejection such as inactive vendor, unsubmitted order, or
  over-receipt?
- What happens when a receipt completes the final remaining quantity across all open
  lines on the order?

### Edge Case Resolutions

- Retrying a previously successful create, submit, or receive request with the same
  idempotency key and the same semantic request payload returns the original logical
  success outcome without creating duplicate effects.
- Reusing an idempotency key for a different create, submit, or receive request is a
  permanent caller error and MUST be rejected with a stable machine-readable business
  error rather than surfaced as a retryable infrastructure failure.
- A goods receipt requested for any order state other than `SUBMITTED` MUST be
  rejected as an invalid workflow state.
- Temporary persistence failures MUST be surfaced as retryable infrastructure errors,
  while inactive vendor, invalid state, over-receipt, and idempotency-key conflict
  cases MUST be surfaced as non-retryable business errors.
- When an accepted goods receipt completes the final remaining quantity on every open
  order line, the purchase order transitions to `RECEIVED` and does not move to
  `CLOSED` in this feature.

## Requirements _(mandatory)_

### Functional Requirements

- **FR-001**: The system MUST allow an agent to create a purchase order against an
  active vendor by specifying one or more line items with the requested goods,
  quantities, and agreed unit prices.
- **FR-002**: The system MUST reject purchase-order creation for a vendor that is
  inactive or missing, using a machine-readable business error.
- **FR-003**: The system MUST require at least one line item for draft purchase-order
  creation.
- **FR-004**: The system MUST reject purchase-order lines with non-positive quantity
  or non-positive unit-price values.
- **FR-005**: The system MUST create a new purchase order in a draft state that is
  distinct from the state required for goods receipt.
- **FR-006**: The system MUST allow an agent to submit a draft purchase order for
  fulfilment and transition it into a submitted state that is eligible for receiving
  goods.
- **FR-007**: The system MUST reject a submission attempt for an order that is not in
  draft state and identify the current state and required state in structured form.
- **FR-008**: The system MUST prevent goods receipts from being recorded against an
  order that has never been submitted.
- **FR-009**: The system MUST allow goods receipts to be recorded across multiple
  receipt events for the same submitted purchase order.
- **FR-010**: The system MUST accumulate received quantities per order line across all
  recorded receipts.
- **FR-011**: The system MUST reject any goods receipt that would cause cumulative
  received quantity on any order line to exceed the ordered quantity.
- **FR-012**: The system MUST preserve previously accepted receipt records when a new
  receipt attempt is rejected.
- **FR-013**: The system MUST automatically recognize when all order lines have been
  fully received and reflect that completion in the order's returned state.
- **FR-014**: The system MUST allow an agent to retrieve the full state of a purchase
  order, including overall order status, vendor reference, receipt history, and
  per-line ordered, received, and remaining quantities.
- **FR-015**: The system MUST provide enough structured response information for an
  agent to determine whether an order is ready for further invoicing activity,
  partially fulfilled, or still pending additional receipts.
- **FR-016**: The system MUST distinguish at least the following permanent business
  conditions in structured form: vendor not found, vendor inactive, order not found,
  order not in draft state for submission, order not submitted for receipt, and
  over-receipt attempt.

### API Contract & Recovery Requirements _(mandatory for APIs)_

- The purchase-order creation capability must accept a vendor reference and one or
  more line items and return the created order identifier, current state, and line
  details.
- The purchase-order submission capability must return the order identifier, the new
  submitted state, and confirmation that the order is now eligible for fulfilment and
  goods receipt.
- The goods-receipt recording capability must accept an order reference and one or
  more received line quantities and return cumulative receipt progress and remaining
  outstanding quantities after the receipt is accepted.
- The order-state query capability must return the overall order state plus per-line
  progress values, receipt history, and vendor context sufficient for a calling agent
  to determine invoicing readiness.
- Each mutating capability must define idempotency expectations so a retried request
  does not create duplicate orders, duplicate submissions, or duplicate receipt
  effects.
- Failure responses must use stable machine-readable codes and indicate whether the
  failure is retryable, correctable by the caller, or terminal.
- Reusing an idempotency key for a different semantic request MUST return a stable
  non-retryable business error so an agent can distinguish caller correction from a
  transient dependency retry.
- All contract responses must carry identifiers and telemetry fields required to
  correlate order creation, submission, and receipt events across retries.
- The workflow state model must explicitly define at least the draft, submitted,
  received, and later closed states, along with the allowed transitions between
  them.

### Key Entities _(include if feature involves data)_

- **Purchase Order**: A procurement commitment against a specific vendor that moves
  through states from creation to fulfilment-readiness and receipt completion.
- **Purchase Order Line Item**: A requested SKU or material on a purchase order,
  including description, ordered quantity, unit price, and cumulative receipt
  progress.
- **Goods Receipt**: A delivery event recorded against a submitted purchase order,
  potentially covering only part of one or more order lines and carrying receipt
  event context.
- **Receipt Progress View**: A derived machine-readable summary showing cumulative
  received and remaining quantities per purchase-order line.

## Out Of Scope

- Cancelling or amending a submitted purchase order
- Recording returns or rejections of previously received goods
- Partial submission of only some order lines while others remain unsubmitted
- Invoice creation, invoice matching, or invoice approval logic

## Success Criteria _(mandatory)_

### Measurable Outcomes

- **SC-001**: In representative validation scenarios, 100% of submitted purchase
  orders can be queried with complete per-line ordered, received, and remaining
  quantities after any accepted receipt sequence.
- **SC-002**: In representative validation scenarios, 100% of attempts to record
  goods against orders that were never submitted are rejected before any receipt is
  stored.
- **SC-003**: In representative validation scenarios, 100% of over-receipt attempts
  are rejected without causing cumulative received quantity to exceed ordered
  quantity on any line.
- **SC-004**: Procurement agents can determine whether a purchase order is ready for
  invoicing in no more than one dedicated order-state query per order.
- **SC-005**: In representative validation scenarios, agents complete purchase-order
  creation, submission, receipt recording, and state assessment without human
  intervention in at least 95% of requests using valid business inputs and available
  system data.
- **SC-006**: In representative validation scenarios involving transient failures,
  agents correctly distinguish retryable infrastructure failures from permanent
  business rejections and recover with the correct next action in at least 95% of
  affected requests.

## Assumptions

- Vendor eligibility is determined by the existing vendor-management capability and
  only active vendors are allowed to receive new purchase orders.
- Invoice creation and invoice matching are out of scope for this feature; this
  feature only provides the order and receipt information needed to decide whether
  invoicing may proceed.
- Ordered goods can be represented as discrete purchase-order line items, each with
  its own quantity and agreed unit price.
- Goods receipts are recorded cumulatively against purchase-order lines rather than
  replacing prior receipt history.

## Assignment Alignment

Intentional deviations from the original assignment are documented in
`enhancement.md` for this feature.
