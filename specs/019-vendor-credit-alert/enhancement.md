# Enhancement Notes: Vendor Credit Alert

## Purpose

This document answers two questions for this feature: what the original assignment
actually requested, and where this repository intentionally sharpens or extends that
request so the result is machine-friendly and defensible in an interview discussion.

## Alignment With The Original Assignment

### 1. The async vendor credit-risk signal is part of the original assignment

The original assignment lists as a stretch goal an async background task that flags
invoices where the vendor's total open AP exceeds the credit limit. This feature keeps
that core idea intact: the signal is asynchronous, non-blocking, and based on vendor
open AP versus credit limit.

**Why**:

- The assignment explicitly names this business problem, so the feature is grounded in
  the interview prompt rather than invented from scratch.
- Preserving the async, non-blocking behavior is consistent with the repo's
  machine-first workflow style and the original stretch-goal wording.

## Deviations And Enhancements

### 2. The repository upgrades the stretch goal into a fully machine-actionable workflow

The original assignment asks only for an async background task that flags the condition.
This feature adds a durable `credit_check_id`, a persisted `CreditCheckRecord`, and
`GET /credit-checks/{id}` so an agent can deterministically inspect state instead of
guessing whether the background work has finished.

**Why**:

- A machine-first API needs a queryable handle, not just a side effect hidden in logs
  or persistence.
- This makes the async workflow observable and replay-safe without changing the caller's
  success path.

### 3. The repository uses a vendor-level active alert instead of literally flagging each invoice

The original assignment says to flag invoices where vendor open AP exceeds the credit
limit. This implementation stores one current active alert per vendor and correlates it
back to the triggering invoice and credit check.

**Why**:

- The breach condition is vendor-wide, not unique to a single invoice.
- A vendor-level alert avoids duplicate active records when multiple invoices trip the
  same risk state.
- Vendor exposure is already the natural checkpoint for reviewing vendor-wide risk.

**Defensibility**:

- This is a bounded, machine-friendly representation of the same business risk.
- The ADR documents the tradeoff explicitly so the deviation is reviewable, not hidden.

### 4. The repository narrows the alert surface to the next natural checkpoint

The original assignment says the feature should flag the condition asynchronously, but
it does not define how an agent should retrieve that signal later. This implementation
surfaces the active alert through the existing vendor exposure endpoint rather than
introducing a separate alert router.

**Why**:

- The repo already has a vendor exposure checkpoint that fits the decision moment.
- Reusing that surface keeps the API smaller and more coherent for agent callers.

### 5. The repository adds replay-safe semantics beyond the assignment text

The original assignment does not say what should happen if a create or approve request
is retried with the same idempotency key after the background check has already been
scheduled. This implementation stores the generated `credit_check_id` with the original
logical success and replays the same identifier on retry without scheduling duplicate
background work.

**Why**:

- Agent-facing APIs need deterministic replay behavior.
- Without this rule, retries could create duplicate checks and conflicting alert state.

### 6. The repository defines alert-clear behavior explicitly

The original assignment describes when to raise the condition but does not define how a
later non-breached evaluation should behave. This implementation clears the current
active alert when a later completed check finds exposure at or below the credit limit.

**Why**:

- A current-state alert model is only defensible if stale risk is removed when the
  vendor is no longer above the limit.
- This keeps vendor exposure responses truthful to the current risk state.

## Best-Practice Assessment

### Implementation best-practice view

- Strong: durable async handle, replay-safe scheduling, deterministic query endpoint,
  bounded alert model, and contract-plus-integration tests.
- Reasonable PoC tradeoff: FastAPI `BackgroundTasks` is acceptable in this repo because
  the contract is durable even though execution is in-process.
- Known limitation: there is no historical alert archive or external worker queue, but
  both are appropriately out of scope for this interview slice.

### Enhancement best-practice view

- Strong: every enhancement is tied to agent-first behavior, determinism, or bounded
  state management.
- Strong: the biggest deviation, vendor-level alerts, is documented explicitly in ADR
  form rather than smuggled into code.
- Strong: enhancements do not block or distort the original business workflows.
