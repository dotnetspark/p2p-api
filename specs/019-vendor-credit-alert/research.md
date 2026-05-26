# Research: Vendor Credit Alert

## Decision: Pre-create a durable `CreditCheckRecord` before dispatching FastAPI `BackgroundTasks`

**Rationale**: The caller needs a deterministic follow-up handle even though the work
runs after the response is sent. Creating the record first with a UUID identifier and
`PENDING` status gives the request path something durable to return immediately and
gives the background task a stable row to complete later.

**Alternatives considered**:

- Generate the identifier inside the background task: rejected because the caller would
  have nothing deterministic to query in the original response.
- Track in-flight work only in memory: rejected because it would break replay safety
  and would not survive process restarts.

## Decision: Use FastAPI `BackgroundTasks` from successful invoice create and approve handlers

**Rationale**: The feature explicitly requires the credit check to run after the
response is sent and never delay the parent request. FastAPI `BackgroundTasks`
matches that behavior in the existing single-process service without introducing a
worker tier or transport abstraction.

**Alternatives considered**:

- Inline synchronous check: rejected because it would couple response latency and
  failure handling to the exposure evaluation.
- External queue or worker service: rejected because it adds unnecessary infrastructure
  complexity for the current PoC scope.

## Decision: Catch and log background-task exceptions silently

**Rationale**: Task failures must never surface to the caller or convert a failed
action into a success. The background task therefore needs local exception handling
with structured logging, leaving the original create or approve outcome untouched.

**Alternatives considered**:

- Bubble exceptions into the request lifecycle: rejected because the response must be
  unaffected once the parent action succeeds.
- Expose task failures through the original response: rejected because the feature is
  advisory and explicitly decoupled.

## Decision: Expose `GET /credit-checks/{id}` from the existing invoices router module

**Rationale**: The user wants no new router while still requiring a query endpoint.
Adding the public path to the existing invoices route module keeps the code change
localized and avoids another router registration, while the external path remains a
top-level machine-readable resource.

**Alternatives considered**:

- Add a separate credit-check router: rejected because it increases interface surface
  area and violates the requested scope boundary.
- Omit the query endpoint and rely only on vendor exposure polling: rejected because it
  leaves the agent unable to determine whether a specific check has completed.

## Decision: Return the credit-check identifier in a top-level `credit_check_id` response field

**Rationale**: Existing shipped features use top-level response fields, not a nested
metadata envelope. Returning a single `credit_check_id` at the top level preserves the
current response style while still giving the agent a deterministic handle for
`GET /credit-checks/{id}`.

**Alternatives considered**:

- Add alert fields directly to create and approve responses: rejected because the check
  completes later and the feature is intentionally non-blocking.
- Introduce `meta.next_actions`: rejected because no existing feature uses that
  envelope shape and it would create an unnecessary contract inconsistency.
- Reuse the existing single `next_action` string: rejected because it would overload an
  established workflow field that already points to the next business action.

## Decision: Compute outstanding AP as the sum of invoice amounts in `PENDING`, `MATCHED`, and `APPROVED`

**Rationale**: The reviewed spec and prior vendor exposure feature already treat those
statuses as unpaid obligations. Reusing the same definition preserves consistency
between the background check and the vendor exposure endpoint.

**Alternatives considered**:

- Include `PAID` invoices: rejected because paid invoices are no longer open vendor
  obligations.
- Include only approved invoices: rejected because pending and matched invoices still
  represent open AP exposure in this repo's workflow.

## Decision: Persist a single current `CreditAlert` per vendor and replace it on newer breaches

**Rationale**: The feature is for live risk signalling, not historical audit. A single
active record per vendor satisfies the reviewed spec, avoids unbounded accumulation,
and keeps vendor exposure responses simple.

**Alternatives considered**:

- Keep one alert per triggering invoice: rejected because the original brief's
  invoice-level phrasing would create redundant records for the same vendor-wide risk
  condition.
- Append historical alerts indefinitely: rejected because history is out of scope for
  this phase.

## Decision: Clear any existing active alert when the latest completed check is at or below the limit

**Rationale**: The external contract says vendor exposure is unchanged when no active
breach exists. Clearing stale alerts on a later non-breach check keeps the endpoint's
current-state semantics consistent with the reviewed spec.

**Alternatives considered**:

- Leave the last breach visible indefinitely: rejected because it would present stale
  risk after obligations fall back below the limit.
- Add a resolved alert history model: rejected because historical tracking is out of
  scope.

## Decision: Keep the credit-check query response minimal: `status`, `breached`, and `alert_id`

**Rationale**: The query endpoint exists to tell the agent whether the background check
is still pending and whether it resulted in an alert. Returning `alert_id` only when a
breach exists gives a stable handoff to the alert/exposure view without embedding
decision instructions in the query payload.

**Alternatives considered**:

- Return a full alert object from the query endpoint: rejected because vendor exposure
  is the natural checkpoint for full context.
- Add `agent_instruction`: rejected because the latest reviewed spec removes
  decision-prescriptive instructions from this feature slice.

## Decision: Extend vendor exposure with an optional `active_credit_alert` object containing escalation context only

**Rationale**: The finance agent already uses vendor exposure as a natural checkpoint.
Extending that endpoint avoids a new retrieval surface and keeps below-limit responses
identical by omitting the field entirely when no alert exists.

**Alternatives considered**:

- Add a dedicated credit-alert endpoint: rejected because the existing vendor exposure
  endpoint is already the intended checkpoint.
- Return an empty alert object below the threshold: rejected because omission is a
  clearer machine-readable signal that no active alert exists.

## Decision: Prevent duplicate background checks on idempotent replay by dispatching only on the first logical success

**Rationale**: The reviewed spec requires replay safety. Existing idempotency logic in
the invoice flows already distinguishes first execution from replay, so scheduling
must happen only when the original logical success is committed and the existing
`credit_check_id` can be reused.

**Alternatives considered**:

- Schedule the task again on every replay: rejected because it would duplicate side
  effects despite a stable response.
- Ignore idempotency and deduplicate later in the task alone: rejected because it
  still wastes work and complicates observability.

## Decision: Document vendor-level alerting as an ADR-backed deviation from the assignment's invoice phrasing

**Rationale**: The original assignment says the async task "flags invoices," but the
reviewed spec intentionally uses a vendor-level current-state alert because the risk
condition is vendor-wide exposure, not a property unique to one invoice.

**Alternatives considered**:

- Follow invoice-level flagging literally: rejected because it multiplies records for a
  single vendor-wide breach state and weakens the checkpoint retrieval model.
