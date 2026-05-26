---
description: "Task list for vendor credit alert implementation"
---

# Tasks: Vendor Credit Alert

**Input**: Design documents from `/specs/019-vendor-credit-alert/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/vendor-credit-alert.openapi.yaml, quickstart.md

**Tests**: Contract and integration tests are REQUIRED for stories that change externally visible API behavior, response payloads, workflow transitions, or machine-readable error semantics.

**Organization**: Tasks are grouped by user story so each story can be implemented and validated independently once prerequisites are complete.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel if the task touches different files and has no dependency on an unfinished task
- **[Story]**: User story label for story-phase tasks only
- Every task includes the exact file path it should change or validate

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Prepare the new credit-check modules and API surfaces without changing runtime behavior yet.

- [x] T001 Create credit-check and credit-alert module scaffolding in src/persistence/models/credit_check.py, src/persistence/models/credit_alert.py, src/persistence/repositories/credit_check_repository.py, src/persistence/repositories/credit_alert_repository.py, and src/domain/services/vendor_credit_alert_service.py
- [x] T002 [P] Prepare response and query schema scaffolding for `credit_check_id`, credit-check status, and `active_credit_alert` in src/api/schemas/invoice.py and src/api/schemas/vendor_exposure.py
- [x] T003 [P] Prepare route scaffolding for background-task wiring and `GET /credit-checks/{creditCheckId}` in src/api/routes/invoices.py and src/api/routes/vendor_exposure.py

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Establish the shared persistence, domain, idempotency, and observability primitives required by all user stories.

**⚠️ CRITICAL**: No user story work should begin until this phase is complete.

- [x] T004 Add the `CreditCheckRecord` ORM table, status fields, and timestamps in src/persistence/models/credit_check.py
- [x] T005 [P] Add the `CreditAlert` ORM table, vendor-scoped active-record constraints, and foreign-key relationships in src/persistence/models/credit_alert.py
- [x] T006 [P] Add credit-check and credit-alert domain entities and status helpers in src/domain/models/vendor_credit.py
- [x] T007 Implement credit-check persistence create, get, replay-lookup, and completion updates in src/persistence/repositories/credit_check_repository.py
- [x] T008 [P] Implement active alert upsert and clear operations in src/persistence/repositories/credit_alert_repository.py
- [x] T009 [P] Extend outstanding AP aggregation and triggering-invoice lookups in src/persistence/repositories/invoice_repository.py
- [x] T010 [P] Extend idempotent replay storage so invoice create and approve can preserve `credit_check_id` in src/persistence/repositories/idempotency_repository.py and src/persistence/repositories/invoice_repository.py
- [x] T011 [P] Add credit-check error codes, status constants, and silent background-task logging hooks in src/core/errors.py and src/domain/services/vendor_credit_alert_service.py
- [x] T012 Ensure the new credit-check tables participate in startup and test database creation in src/main.py and tests/conftest.py

**Checkpoint**: Shared credit-check persistence, domain types, and replay support are ready for story implementation.

---

## Phase 3: User Story 1 - Trigger Non-Blocking Exposure Checks (Priority: P1) 🎯 MVP

**Goal**: Return a top-level `credit_check_id` from successful invoice create and approve actions while scheduling the credit evaluation after the response is sent.

**Independent Test**: Create or approve an invoice, verify the response still returns the existing business payload plus a top-level `credit_check_id`, verify a pending credit-check record exists, and confirm idempotent replay returns the same identifier without duplicate scheduling.

### Tests for User Story 1 ⚠️

> **NOTE**: Write these tests first and ensure they fail before implementation.

- [x] T013 [P] [US1] Add contract coverage for `POST /invoices` returning top-level `credit_check_id` and replay reuse in tests/contract/test_invoice_registration.py
- [x] T014 [P] [US1] Add contract coverage for `POST /invoices/{invoice_id}/approve` returning top-level `credit_check_id` and replay reuse in tests/contract/test_invoice_approval.py
- [x] T015 [P] [US1] Add integration coverage for pending credit-check creation, post-response dispatch, and replay-safe identifier reuse in tests/integration/test_vendor_credit_alert.py

### Implementation for User Story 1

- [x] T016 [US1] Implement shared pending credit-check creation and background-task dispatch orchestration in src/domain/services/vendor_credit_alert_service.py
- [x] T017 [US1] Invoke credit-check scheduling from invoice create and approve flows in src/domain/services/invoice_service.py and src/domain/services/invoice_approval_service.py
- [x] T018 [US1] Serialize top-level `credit_check_id` on create and approve responses in src/api/schemas/invoice.py and src/api/routes/invoices.py

**Checkpoint**: User Story 1 is functional and independently testable as the MVP slice.

---

## Phase 4: User Story 2 - Record Breached Credit Alerts (Priority: P2)

**Goal**: Complete background credit checks, persist breach outcomes, and maintain one active alert per vendor.

**Independent Test**: Trigger create or approve for a vendor over the credit limit, verify the background task completes the credit-check record, writes one active alert with breach context, leaves callers unaffected, and replaces or clears alerts correctly on later checks.

### Tests for User Story 2 ⚠️

- [x] T019 [P] [US2] Add integration coverage for breached alerts, non-breached completion, and single-active-alert replacement in tests/integration/test_vendor_credit_alert.py

### Implementation for User Story 2

- [x] T020 [US2] Implement background credit evaluation, breach calculation, and completed credit-check persistence in src/domain/services/vendor_credit_alert_service.py
- [x] T021 [US2] Implement active-alert replacement and stale-alert clearing in src/persistence/repositories/credit_alert_repository.py and src/persistence/repositories/credit_check_repository.py
- [x] T022 [US2] Catch and log background task exceptions without affecting caller-visible outcomes in src/domain/services/vendor_credit_alert_service.py and src/api/routes/invoices.py

**Checkpoint**: User Story 2 is independently testable and produces durable alert state without changing the triggering workflow outcome.

---

## Phase 5: User Story 4 - Query Credit Check Outcome by Identifier (Priority: P2)

**Goal**: Let agents query `GET /credit-checks/{creditCheckId}` to determine whether the background task is pending or completed and whether it produced an alert.

**Independent Test**: Trigger a credit check, query it before completion to see `PENDING`, query it after completion to see `COMPLETED`, and verify breached checks return the linked `alert_id` while missing identifiers return the correct machine-readable error.

### Tests for User Story 4 ⚠️

- [x] T023 [P] [US4] Add contract coverage for `GET /credit-checks/{creditCheckId}` pending, completed, breached, and not-found outcomes in tests/contract/test_credit_check_query.py
- [x] T024 [P] [US4] Add integration coverage for credit-check lifecycle queries and alert correlation in tests/integration/test_credit_check_query.py

### Implementation for User Story 4

- [x] T025 [US4] Implement credit-check query orchestration and not-found handling in src/domain/services/vendor_credit_alert_service.py and src/persistence/repositories/credit_check_repository.py
- [x] T026 [US4] Expose `GET /credit-checks/{creditCheckId}` and response serialization in src/api/routes/invoices.py and src/api/schemas/invoice.py

**Checkpoint**: User Story 4 is independently testable and gives agents deterministic visibility into background check state.

---

## Phase 6: User Story 3 - Retrieve Active Alerts At the Next Checkpoint (Priority: P3)

**Goal**: Extend vendor exposure so agents can retrieve the current active alert context before making an approval decision, while below-threshold responses remain unchanged.

**Independent Test**: After a breached check, request vendor exposure and verify `active_credit_alert` is present with alert context; after a non-breached or cleared state, verify the response omits the alert field entirely.

### Tests for User Story 3 ⚠️

- [x] T027 [P] [US3] Add contract coverage for `active_credit_alert` inclusion and omission in tests/contract/test_vendor_exposure.py
- [x] T028 [P] [US3] Add integration coverage for vendor exposure alert context after breach and after resolution in tests/integration/test_vendor_exposure.py

### Implementation for User Story 3

- [x] T029 [US3] Extend vendor exposure loading to include current active credit alert context in src/domain/services/vendor_exposure_service.py and src/persistence/repositories/credit_alert_repository.py
- [x] T030 [US3] Serialize `active_credit_alert` without changing below-threshold responses in src/api/schemas/vendor_exposure.py and src/api/routes/vendor_exposure.py

**Checkpoint**: User Story 3 is independently testable and surfaces the current alert only at the intended vendor exposure checkpoint.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Finalize the contract docs, release notes, and validation pass for the full feature.

- [x] T031 [P] Update credit-check and vendor-alert examples plus recovery semantics in specs/019-vendor-credit-alert/contracts/vendor-credit-alert.openapi.yaml and specs/019-vendor-credit-alert/quickstart.md
- [x] T032 [P] Add the unreleased vendor credit alert entry in CHANGELOG.md
- [x] T033 Run the targeted regression suite covering tests/contract/test_invoice_registration.py, tests/contract/test_invoice_approval.py, tests/contract/test_credit_check_query.py, tests/contract/test_vendor_exposure.py, tests/integration/test_vendor_credit_alert.py, tests/integration/test_credit_check_query.py, and tests/integration/test_vendor_exposure.py

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies. Can start immediately.
- **Foundational (Phase 2)**: Depends on Setup completion. Blocks all user stories.
- **User Story 1 (Phase 3)**: Depends on Foundational completion.
- **User Story 2 (Phase 4)**: Depends on User Story 1 because alert completion relies on the scheduled credit-check workflow.
- **User Story 4 (Phase 5)**: Depends on User Story 1 for identifier creation and on User Story 2 for breached alert correlation behavior.
- **User Story 3 (Phase 6)**: Depends on User Story 2 because vendor exposure only surfaces active alerts once they are persisted.
- **Polish (Phase 7)**: Depends on all desired user stories being complete.

### User Story Dependencies

- **US1**: No dependency on other stories after Foundational; this is the MVP.
- **US2**: Requires US1 because background completion depends on a created pending `CreditCheckRecord`.
- **US4**: Requires US1 for `credit_check_id` generation and US2 for meaningful breached-state query validation.
- **US3**: Requires US2 because vendor exposure only surfaces persisted active alerts.

### Within Each User Story

- Contract and integration tests must be written and fail before implementation for API-facing changes.
- Shared domain and persistence changes must be complete before route wiring depends on them.
- Background task orchestration must exist before story-specific route or response mapping is finalized.
- Validate each story independently before moving to the next priority.

### Parallel Opportunities

- **Setup**: T002 and T003 can run in parallel.
- **Foundational**: T005, T006, T008, T009, T010, and T011 can run in parallel after T004 establishes the shared table vocabulary.
- **US1**: T013, T014, and T015 can run in parallel.
- **US4**: T023 and T024 can run in parallel.
- **US3**: T027 and T028 can run in parallel.
- **Polish**: T031 and T032 can run in parallel before T033.

---

## Parallel Example: User Story 1

```text
Task: "T013 Add contract coverage for POST /invoices returning top-level credit_check_id and replay reuse in tests/contract/test_invoice_registration.py"
Task: "T014 Add contract coverage for POST /invoices/{invoice_id}/approve returning top-level credit_check_id and replay reuse in tests/contract/test_invoice_approval.py"
Task: "T015 Add integration coverage for pending credit-check creation, post-response dispatch, and replay-safe identifier reuse in tests/integration/test_vendor_credit_alert.py"
```

## Parallel Example: User Story 4

```text
Task: "T023 Add contract coverage for GET /credit-checks/{creditCheckId} pending, completed, breached, and not-found outcomes in tests/contract/test_credit_check_query.py"
Task: "T024 Add integration coverage for credit-check lifecycle queries and alert correlation in tests/integration/test_credit_check_query.py"
```

## Parallel Example: User Story 3

```text
Task: "T027 Add contract coverage for active_credit_alert inclusion and omission in tests/contract/test_vendor_exposure.py"
Task: "T028 Add integration coverage for vendor exposure alert context after breach and after resolution in tests/integration/test_vendor_exposure.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup.
2. Complete Phase 2: Foundational.
3. Complete Phase 3: User Story 1.
4. Stop and validate invoice create and approve responses independently before moving on.

### Incremental Delivery

1. Finish Setup and Foundational to establish credit-check persistence, replay support, and shared error handling.
2. Deliver US1 and validate post-response scheduling plus `credit_check_id` replay semantics.
3. Deliver US2 and validate breach detection plus single-active-alert behavior.
4. Deliver US4 and validate query-by-identifier state transitions.
5. Deliver US3 and validate vendor exposure alert retrieval.
6. Finish Polish with contract docs, release notes, and targeted regression validation.

### Parallel Team Strategy

1. One developer handles the new ORM and repository modules while another prepares the API schema and route scaffolding.
2. After Foundational completes, one lane can own contract tests while another owns integration tests for each story.
3. US4 query work and US3 vendor exposure work can be split after US2 stabilizes because they touch different API surfaces.

---

## Notes

- All tasks follow the required checklist format: checkbox, task ID, optional `[P]`, required story label for story phases, and exact file paths.
- Contract and integration tests are included wherever the feature changes externally visible API behavior, idempotent replay semantics, or machine-readable response shapes.
- The existing ADR in docs/adr/019-vendor-credit-alert-model.md already satisfies the schema-governance prerequisite for the vendor-level alert design.
- The suggested MVP scope is User Story 1 only.
