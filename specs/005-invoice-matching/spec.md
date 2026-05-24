# Feature Specification: Invoice Matching

**Feature Branch**: `005-invoice-matching`

**Created**: 2026-05-24

**Status**: Draft

**Input**: User description: "A finance agent needs to register an invoice from a vendor against a specific purchase order and verify that the invoice amount is supported by goods actually received — not just ordered. If the invoice exceeds what has been received the agent must be told the exact shortfall and what to do next. If goods are only partially received but the invoice is within the received value the agent should be warned about open exposure but not blocked from proceeding. The same invoice reference from the same vendor cannot be registered twice."

## Context

This feature covers the invoice-registration and invoice-matching slice of the P2P
workflow. It allows a finance agent to record an invoice against a specific purchase
order, verify that the invoice amount is supported by value already received, and
distinguish between hard blocking mismatch conditions and non-blocking residual
exposure warnings.

Within this repository the slice is numbered `005` because vendor management and
purchase-order lifecycle were split into earlier independently verified features.
Business-wise, this is the same invoice-matching control described in the original
assignment's invoice feature.

It depends on the existing vendor-management capability for vendor identity, and on
the purchase-order lifecycle capability for order, receipt, and received-value
progress.

## Actors

- **Finance Agent**: Registers invoices against specific purchase orders, requests
  match evaluation, and decides whether to proceed or wait based on blocking shortfall
  details or non-blocking open-exposure warnings.
- **Procurement Agent**: May consume partial-receipt warning context when remaining
  fulfilment exposure needs follow-up.

## User Scenarios & Testing _(mandatory)_

### User Story 1 - Register Invoice Against A Purchase Order (Priority: P1)

As a finance agent, I want to register an invoice from a vendor against a specific
purchase order so that the invoice can enter the payable workflow with an explicit
link to the commercial obligation it claims to bill.

**Why this priority**: Matching cannot happen until the invoice exists and is tied to
the exact purchase order it is claiming against.

**Independent Test**: Can be fully tested by registering a valid invoice for an
existing vendor and purchase order and verifying that the invoice is stored once with
its vendor reference, purchase-order reference, invoice reference, amount, and initial
workflow state.

**Acceptance Scenarios**:

1. **Given** an existing vendor and a specific purchase order, **When** the agent
   registers an invoice with an invoice reference and amount, **Then** the system
   stores one invoice linked to that vendor and purchase order.
2. **Given** an invoice reference already exists for the same vendor, **When** the
   agent attempts to register the same vendor invoice reference again, **Then** the
   system rejects the duplicate registration and does not create a second invoice.
3. **Given** an invoice registration request is retried with the same idempotency key
   and the same semantic request, **When** the agent repeats the request, **Then** the
   system returns the original logical success outcome without creating a duplicate
   invoice.
4. **Given** a valid invoice registration succeeds, **When** the system returns the
  result, **Then** the invoice begins in a pending state and is not yet matched or
  approved.
5. **Given** a valid invoice registration succeeds, **When** the system returns the
  result, **Then** it tells the agent that the next step is to request invoice matching.

---

### User Story 2 - Block Invoice Amounts Above Received Value (Priority: P1)

As a finance agent, I want the system to reject an invoice that exceeds the value of
goods actually received so that the organisation is never asked to pay for goods that
have not yet arrived.

**Why this priority**: Financial correctness requires blocking overbilling against
receipt progress rather than trusting ordered quantity alone.

**Independent Test**: Can be fully tested by registering an invoice whose amount is
greater than the current received value for the linked purchase order and verifying
that the match attempt is rejected with the exact shortfall and a machine-usable next
action.

**Acceptance Scenarios**:

1. **Given** a purchase order has received goods whose total value is less than the
   invoice amount, **When** the agent requests invoice matching, **Then** the system
   rejects the match and reports the exact monetary shortfall between invoice amount
   and received value.
2. **Given** an invoice match is rejected because received value is insufficient,
   **When** the system returns the result, **Then** it tells the agent whether the
   next action is to wait for additional goods receipt or to correct the invoice.
3. **Given** an invoice is linked to a purchase order that has no received goods
   value yet, **When** the agent requests matching, **Then** the system rejects the
   match as unsupported by receipt progress and reports the full uncovered amount.

---

### User Story 3 - Warn On Partial Receipt Exposure Without Blocking (Priority: P2)

As a finance agent, I want the system to warn me when a match succeeds only because
the current received value happens to cover the invoice while the purchase order is
still partially open so that I can proceed with awareness of remaining fulfilment
exposure.

**Why this priority**: The hard control is preventing payment beyond received value,
but agents also need visibility into residual receipt risk before progressing the
invoice workflow.

**Independent Test**: Can be fully tested by matching an invoice whose amount is
within current received value while the linked purchase order still has outstanding
unreceived quantity and verifying that the match succeeds with a non-blocking warning.

**Acceptance Scenarios**:

1. **Given** a purchase order is only partially received but the current received
   value is still greater than or equal to the invoice amount, **When** the agent
   requests invoice matching, **Then** the system allows the match to succeed and
   returns a warning that fulfilment remains open.
2. **Given** a successful match on a partially received purchase order, **When** the
   system returns the result, **Then** it reports enough structured context about open
  receipt exposure for the agent to decide whether to proceed immediately or wait,
  including the specific open lines and how much remains open on each one.
3. **Given** all ordered goods have been fully received and the invoice amount is
   within received value, **When** the agent requests matching, **Then** the system
   returns a clean successful match result without an open-exposure warning.

### Resolved Clarifications

- A previously matched invoice may be matched again later after additional goods are
  received. Replaying the same semantic request with the same idempotency key returns
  the original logical result; requesting a fresh evaluation after receipt progress
  changes requires a new idempotency key.
- An invoice amount exactly equal to the current received value is not an overbilling
  condition. It is still a warning outcome if any purchase-order lines remain open,
  and it is a clean match only when all lines are fully received.

### Edge Cases

- What happens when the same invoice-registration or invoice-match request is retried
  with the same idempotency key after the original request already succeeded?
- How does the system respond when an invoice references a purchase order that exists
  but belongs to a different vendor than the invoice registration request?
- How does the system distinguish a duplicate invoice reference for the same vendor
  from a transient persistence failure during invoice registration?
- What happens when the invoice amount is exactly equal to the currently received
  goods value on a purchase order that still has outstanding unreceived quantity?
- How does the system respond when receipt progress changes between invoice
  registration and invoice matching?

## Requirements _(mandatory)_

### Functional Requirements

- **FR-001**: The system MUST allow a finance agent to register an invoice against a
  specific vendor and a specific purchase order.
- **FR-002**: The system MUST reject invoice registration when the same invoice
  reference has already been registered for the same vendor.
- **FR-003**: The system MUST allow the same invoice reference string to exist for
  different vendors only if each registration remains unambiguous to the caller.
- **FR-004**: The system MUST persist enough invoice data for later match evaluation,
  including vendor reference, purchase-order reference, invoice reference, amount,
  workflow state, and the most recent match outcome.
- **FR-005**: The system MUST evaluate invoice matching against goods actually
  received rather than against ordered quantity alone.
- **FR-006**: The system MUST reject invoice matching when invoice amount exceeds the
  current value supported by recorded goods receipts for the linked purchase order.
- **FR-007**: The system MUST report the exact monetary shortfall when invoice amount
  exceeds supported received value.
- **FR-008**: The system MUST return structured next-step guidance when a match is
  blocked because received value is insufficient.
- **FR-009**: The system MUST allow invoice matching to succeed when invoice amount is
  less than or equal to current received value even if the purchase order is only
  partially received.
- **FR-010**: The system MUST return a non-blocking warning when a match succeeds on a
  purchase order that still has open receipt exposure.
- **FR-011**: The system MUST omit the open-exposure warning when the linked purchase
  order has been fully received and the invoice amount is supported.
- **FR-012**: The system MUST reject invoice registration when vendor and
  purchase-order references do not represent a coherent relationship.
- **FR-013**: The system MUST preserve idempotent behavior for invoice registration
  and invoice matching so retried identical requests do not create duplicate effects.
- **FR-014**: The system MUST reject reuse of an idempotency key for a different
  semantic invoice-registration or invoice-match request with a stable
  machine-readable business error.
- **FR-015**: The system MUST distinguish at least the following permanent business
  conditions in structured form: duplicate invoice reference for a vendor, purchase
  order not found, vendor and purchase-order mismatch, invoice amount above received
  value, and invalid invoice workflow state for matching.
- **FR-016**: The system MUST create new invoices in a pending state that is neither
  matched nor approved.
- **FR-017**: The invoice-registration response MUST tell the agent that the next step
  is to request matching for the newly created invoice.
- **FR-018**: Every invoice-match response MUST include invoice amount, total
  received value, the difference between received value and invoice amount, whether
  all purchase-order lines are fully received, and the list of any open lines.
- **FR-019**: A partial-receipt warning outcome MUST identify which specific
  purchase-order lines remain open and the remaining quantity or value on each open
  line.
- **FR-020**: Successful match outcomes MUST tell the agent whether the clear next
  path is to proceed to approval or to wait for additional goods receipt context.

### API Contract & Recovery Requirements _(mandatory for APIs)_

- The invoice-registration capability must accept vendor reference, purchase-order
  reference, invoice reference, invoice amount, and caller correlation data, and must
  return the created invoice identifier, a pending workflow state, and the next action.
- The invoice-match capability must return whether the invoice is blocked or matched,
  the received-value basis used for the decision, and any warning or shortfall details
  required for autonomous next-step handling.
- Blocking match failures must include the exact uncovered amount and a structured
  next action that tells the agent whether to wait for more goods receipt or correct
  the invoice.
- Non-blocking partial-receipt outcomes must include a warning payload that makes open
  exposure explicit without changing the successful nature of the match, including the
  open lines that still remain.
- Every match response must include the difference between received value and invoice
  amount, whether all lines are fully received, and the list of open lines, even when
  the list is empty for a clean match.
- Successful match responses must include machine-usable next-step guidance that tells
  the agent whether it may proceed to approval immediately or should wait for more
  receipts despite the invoice being currently supportable.
- Failure responses must clearly distinguish permanent business conditions from
  retryable infrastructure failures so the agent can choose the correct recovery path.
- The contract must define stable idempotency expectations for invoice registration
  and matching, including replay success for identical requests and non-retryable
  business rejection for conflicting key reuse.
- All responses must carry identifiers and telemetry fields needed to correlate
  invoice registration, invoice matching, purchase-order receipt progress, and
  downstream approval decisions.

### Key Entities _(include if feature involves data)_

- **Invoice**: A vendor billing document linked to a specific purchase order and used
  as the subject of match evaluation.
- **Invoice Match Result**: A machine-readable assessment that captures whether the
  invoice is blocked or matched, the value basis used, exact shortfall when blocked,
  warning details when exposure remains open, and the explicit next action.
- **Received Value Snapshot**: The current receipt-backed monetary support available
  from the linked purchase order at the time a match is attempted.
- **Open Exposure Warning**: A non-blocking signal that some quantity or value on the
  linked purchase order remains unreceived even though the invoice amount is currently
  supportable.
- **Open Line Exposure**: A line-level summary of which purchase-order lines still
  remain open and by how much quantity or value.

## Out Of Scope

- Approving invoices or generating GL entries
- Paying invoices or transitioning purchase orders to `CLOSED`
- Registering multiple invoices against the same purchase order in this PoC slice;
  production systems would normally support that broader lifecycle
- Allocating a single invoice across multiple purchase orders
- Handling vendor credit limits or AP exposure escalation workflows

## Success Criteria _(mandatory)_

### Measurable Outcomes

- **SC-001**: In representative validation scenarios, 100% of invoice match attempts
  that exceed current received value are rejected before the invoice can progress as a
  successful match.
- **SC-002**: In representative validation scenarios, 100% of blocked overbilling
  match responses include the exact uncovered amount required for autonomous recovery.
- **SC-003**: In representative validation scenarios, 100% of successful matches on
  partially received purchase orders include a non-blocking open-exposure warning.
- **SC-004**: In representative validation scenarios, 100% of duplicate invoice
  references for the same vendor are rejected without creating a second invoice.
- **SC-005**: Finance agents can determine whether to proceed, wait for more receipt,
  or correct the invoice from no more than one match response per invoice.
- **SC-006**: In representative validation scenarios, agents complete invoice
  registration and match handling without human intervention in at least 95% of
  requests using valid business inputs and available system data.
- **SC-007**: In representative validation scenarios involving transient failures,
  agents correctly distinguish retryable infrastructure failures from permanent
  business rejections and recover with the correct next action in at least 95% of
  affected requests.

## Assumptions

- Vendor identity and purchase-order receipt progress are already available from the
  existing vendor-management and purchase-order lifecycle features.
- Invoice amount is evaluated as a single aggregate amount against the linked
  purchase order's current received-value support rather than by individual invoice
  line distribution in this feature slice.
- A successful match on partial receipt does not remove the need for later approval;
  it only confirms that the current invoice amount is supportable by received goods.
- Finance agents invoking this feature are authorized to register invoices and view
  receipt-backed support information for the linked purchase order.
