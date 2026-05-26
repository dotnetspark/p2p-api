# Feature Specification: Vendor Credit Alert

**Feature Branch**: `feat/019-vendor-credit-alert`

**Created**: 2026-05-25

**Status**: Completed

**Input**: User description: "When an invoice is created or approved the system must automatically run a background check — decoupled from the response — to determine whether the vendor's total outstanding payment obligations have exceeded their credit limit. If the threshold is breached the condition is flagged by writing an alert record. The finance agent retrieves any active alert through the vendor exposure endpoint at its next natural checkpoint before making an approval decision. The check must never slow or affect the action that triggered it. This feature flags only — it never blocks any action."

## User Scenarios & Testing _(mandatory)_

### User Story 1 - Trigger Non-Blocking Exposure Checks (Priority: P1)

As a finance agent, I want invoice creation and invoice approval to trigger a vendor exposure check in the background so the workflow I just performed never slows down or changes behaviour because of risk evaluation.

**Why this priority**: The feature is only acceptable if it preserves the existing create and approve workflows while still ensuring exposure is checked whenever those obligations advance.

**Independent Test**: Can be fully tested by creating or approving an invoice and verifying that the action completes normally while a separate exposure-check outcome is recorded later without altering the original response.

**Acceptance Scenarios**:

1. **Given** an invoice is created successfully, **When** the action completes, **Then** the system generates a credit check identifier before firing the background check, returns that identifier in a top-level `credit_check_id` response field, and the create response is otherwise unchanged by this feature.
2. **Given** an invoice is approved successfully, **When** the action completes, **Then** the system generates a credit check identifier before firing the background check, returns that identifier in a top-level `credit_check_id` response field, and the approval response is otherwise unchanged by this feature.
3. **Given** the same successful create or approve request is replayed with the same idempotency key, **When** the original logical request already triggered an exposure check, **Then** the replayed response returns the same credit check identifier as the original and does not create duplicate side effects from the original workflow.

---

### User Story 2 - Record Breached Credit Alerts (Priority: P2)

As a finance agent, I want the background exposure check to write an alert record when a vendor's outstanding payment obligations have exceeded the credit limit so risk can be surfaced consistently at the next decision point.

**Why this priority**: A non-blocking check has no value unless a breached condition is persisted somewhere durable enough for the agent to inspect later.

**Independent Test**: Can be fully tested by triggering the exposure check for a vendor whose outstanding obligations exceed the credit limit and verifying that an active alert record is written while the triggering workflow remains successful.

**Acceptance Scenarios**:

1. **Given** the background check finds that the vendor's outstanding payment obligations have exceeded the credit limit, **When** the check completes, **Then** the system writes an active alert record for that vendor.
2. **Given** the background check finds that the vendor's outstanding payment obligations remain at or below the credit limit, **When** the check completes, **Then** the system does not create a new active alert record.
3. **Given** the vendor is already above the credit limit when invoice creation or approval occurs, **When** the background check runs, **Then** the system still records the breached condition as an alert and does not block the completed action that triggered the check.

---

### User Story 3 - Retrieve Active Alerts At the Next Checkpoint (Priority: P3)

As a finance agent, I want the vendor exposure endpoint to surface any active credit alert at the next natural checkpoint before approval so I can decide whether escalation is needed before taking on more risk.

**Why this priority**: Decoupling the check from the create or approve response only works if the risk signal is still available at the moment an agent naturally reviews vendor exposure.

**Independent Test**: Can be fully tested by triggering a breached-condition alert and then retrieving vendor exposure to verify that the active alert is visible with enough context for an approval decision.

**Acceptance Scenarios**:

1. **Given** an active alert record exists for a vendor, **When** the finance agent retrieves vendor exposure before making an approval decision, **Then** the response includes the active alert and enough exposure context to support escalation.
2. **Given** no active alert record exists for a vendor, **When** the finance agent retrieves vendor exposure, **Then** the response remains unchanged by this feature.

---

### User Story 4 - Query Credit Check Outcome by Identifier (Priority: P2)

As a finance agent, I want to query the outcome of a specific credit
check using the identifier returned in the triggering response so
that I can deterministically know whether the background check has
completed and what it found before deciding to proceed.

**Why this priority**: Without a queryable check record the agent
must guess whether the background task has run. The pre-generated
identifier eliminates that ambiguity entirely.

**Independent Test**: Can be fully tested by triggering a background
check, capturing the identifier from the response, and querying it
to verify the status transitions from pending to completed and
reflects the correct breach outcome.

**Acceptance Scenarios**:

1. **Given** a credit check has been triggered but not yet completed,
   **When** the agent queries the check by its identifier, **Then**
   the response indicates the check is in progress and no breach
   determination has been made yet.
2. **Given** a credit check has completed without a breach, **When**
   the agent queries the check by its identifier, **Then** the
   response indicates completion, no breach detected, and no alert
   reference.
3. **Given** a credit check has completed with a breach, **When** the
   agent queries the check by its identifier, **Then** the response
   indicates completion, breach detected, and includes the alert
   reference.

---

### Edge Cases

- What happens when the same successful create or approve request is retried with the same idempotency key after the original request already triggered a background check?
- How does the system respond when invoice creation or approval fails before completion for an unrelated business reason?
- How does the system behave when a vendor has already exceeded the credit limit before invoice creation or approval?
- How does the system surface a breached condition if the finance agent does not query vendor exposure until a later checkpoint?

## Requirements _(mandatory)_

### Functional Requirements

- **FR-001**: The system MUST start a vendor credit exposure check after each successful invoice-creation action.
- **FR-002**: The system MUST start a vendor credit exposure check after each successful invoice-approval action.
- **FR-003**: The credit exposure check MUST run outside the response path of the action that triggered it.
- **FR-004**: The credit exposure check MUST NOT slow, alter, or block the successful create or approve response that triggered it.
- **FR-005**: The credit exposure check MUST evaluate whether the vendor's total outstanding payment obligations have exceeded the vendor's credit limit.
- **FR-006**: When the check finds that outstanding obligations have exceeded the credit limit, the system MUST write an active alert record for that vendor.
- **FR-007**: When the check finds that outstanding obligations remain at or below the credit limit, the system MUST NOT create a new active alert record.
- **FR-008**: The alert record MUST identify the vendor and include the outstanding amount, credit limit, and percentage consumed so the finance agent has enough context to make an escalation decision.
- **FR-009**: The alert record MUST indicate in machine-readable form that the condition is advisory only and does not block workflow actions.
- **FR-010**: The vendor exposure capability MUST surface any active credit alert to the finance agent at the next retrieval checkpoint before an approval decision.
- **FR-011**: If no active credit alert exists for the vendor, the vendor exposure response MUST remain unchanged by this feature.
- **FR-012**: If a vendor is already above the credit limit before invoice creation or approval, the completed triggering action MUST still succeed unless another existing business rule rejects it, and the breached condition MUST still be flagged.
- **FR-013**: The system MUST preserve replay-safe behaviour so an identical retried create or approve request does not change the original business outcome of the triggering action.
- **FR-014**: The system MUST continue to return existing business or infrastructure errors for invalid create or approve requests, and MUST NOT convert a failing operation into a success solely to run a credit exposure check.
- **FR-015**: The system MUST ensure any active alert can be correlated to the vendor, the evaluated exposure condition, and the workflow that caused the check to run.
- **FR-016**: The system MUST generate a credit check identifier before firing the background task and return it in a top-level `credit_check_id` response field. The triggering response does not include `agent_instruction`; it only provides the deterministic identifier the agent uses with `GET /credit-checks/{id}` to query the check outcome.
- **FR-017**: The system MUST provide a capability for the agent to query the outcome of a specific credit check by its identifier, returning the check status (`PENDING` or `COMPLETED`), whether a breach was detected, and any resulting alert reference.
- **FR-018**: The system MUST retain only the most recent active credit alert per vendor in this feature slice; a later breached check replaces the current active alert for that vendor rather than accumulating historical active records.

### API Contract & Recovery Requirements _(mandatory for APIs)_

- The invoice-creation capability must define that successful create responses include a pre-generated `credit_check_id` top-level field, while the existing response data remains otherwise unchanged by this feature.
- The invoice-approval capability must define that successful approval responses include a pre-generated `credit_check_id` top-level field, while the existing response data remains otherwise unchanged by this feature.
- The credit check query capability must define the response shape for all three states: pending (check in progress), completed without breach, and completed with breach including alert reference.
- The vendor exposure capability must define the exact response addition used to surface any active credit alert including the vendor identity, outstanding amount, credit limit, and percentage consumed needed for escalation decisions.
- The contract must define how alert records are represented and how agents distinguish an active credit alert from ordinary vendor exposure data.
- The contract must define how replayed mutating requests return the same credit check identifier as the original while avoiding unintended duplicate side effects from the decoupled check.
- The contract must define how invalid-state or infrastructure failures on the triggering action are reported so agents can distinguish workflow failure from later non-blocking credit-risk signalling.

### Key Entities _(include if feature involves data)_

- **Credit Check Record**: A record created with a pre-generated identifier before the background task fires. Begins in a pending state and is updated to completed when the check finishes. Carries the breach determination and a reference to any resulting alert. Returned in the triggering response as a next action so the agent has a deterministic query endpoint without polling blindly.
- **Vendor Credit Exposure Alert**: An active alert record written when a credit check completes with a breach. Retained as the most recent alert per vendor. Includes outstanding amount, credit limit, and percentage consumed so the finance agent has enough context to decide whether escalation is needed.
- **Outstanding Payment Obligation**: The sum of all invoice amounts for a vendor in `PENDING`, `MATCHED`, or `APPROVED` status - all obligations not yet `PAID`.
- **Credit Exposure Check Trigger**: The successful invoice creation or approval event that causes the pre-generated credit check record to be created and the decoupled background evaluation to run.

## Success Criteria _(mandatory)_

### Measurable Outcomes

- **SC-001**: In representative validation scenarios, 100% of successful invoice-create and invoice-approve responses include a pre-generated top-level `credit_check_id` without adding blocking or changing any existing business response fields.
- **SC-002**: In representative validation scenarios, 100% of credit-limit breaches detected by the decoupled check result in an active alert record and a completed credit check record with breached status.
- **SC-003**: In representative validation scenarios, 100% of non-breached exposure checks result in a completed credit check record with no breach and no new active alert record.
- **SC-004**: In representative validation scenarios, finance agents can retrieve any active credit alert through vendor exposure before an approval decision in at least 95% of breached cases.
- **SC-005**: In representative retry scenarios, 100% of replayed create and approve requests return the same credit check identifier as the original and preserve the original business outcome.
- **SC-006**: In representative validation scenarios, 100% of credit check query responses correctly reflect the current check state - pending while in progress, completed with accurate breach determination when done.

## Assumptions

- Each vendor already has a maintained credit limit available to the workflow at invoice creation and approval time.
- The system already has or can derive a current total outstanding payment obligation for each vendor without introducing a new human approval step.
- The vendor exposure capability already exists (feat/001) and can be extended to surface active credit alerts.
- The breach condition is strictly exceeding the full credit limit - sourced directly from the original assignment. No advisory percentage threshold.
- Outstanding payment obligations include all invoices in `PENDING`, `MATCHED`, or `APPROVED` status - all obligations not yet `PAID`.
- Only the most recent active alert per vendor is retained - this is a monitoring feature not an audit trail. Historical breach records are out of scope for this phase.
- The original assignment says "flags invoices" but a vendor-level alert is the correct model - one alert per vendor avoids unbounded accumulation per invoice. This deviation will be documented as an ADR during planning.
- Blocking or automatically escalating the workflow is out of scope - this feature only flags the condition for later review.
