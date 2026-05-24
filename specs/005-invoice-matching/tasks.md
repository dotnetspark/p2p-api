# Tasks: Invoice Matching

**Input**: Design documents from `/specs/005-invoice-matching/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Contract and integration tests are REQUIRED because this feature adds new API endpoints, workflow transitions, and machine-consumable error semantics.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g. `US1`, `US2`, `US3`)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Prepare shared API and fixture scaffolding for the invoice slice.

- [x] T001 Align invoice-matching seed assumptions in src/persistence/seed/bootstrap.py
- [x] T002 [P] Create invoice API schema scaffolding in src/api/schemas/invoice.py
- [x] T003 [P] Create invoice route scaffolding and register it in src/api/routes/invoices.py and src/api/router.py

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core invoice persistence, domain types, and shared error handling that MUST be complete before any user story can be implemented.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [x] T004 Extend invoice ORM fields and uniqueness constraints for registration workflow in src/persistence/models/invoice.py
- [x] T005 [P] Add invoice match snapshot ORM model in src/persistence/models/invoice_match_snapshot.py
- [x] T006 [P] Add invoice domain models, open-line exposure types, and match result types in src/domain/models/invoice.py
- [x] T007 Extend invoice persistence operations for create, duplicate lookup, get-by-id, and match snapshot replay in src/persistence/repositories/invoice_repository.py
- [x] T008 [P] Add receipt-backed value snapshot queries in src/persistence/repositories/purchase_order_repository.py
- [x] T009 [P] Extend invoice business errors and HTTP status mapping in src/core/errors.py and src/api/dependencies/error_handlers.py
- [x] T010 Ensure invoice models are loaded through startup and seeding paths in src/main.py and src/persistence/seed/bootstrap.py

**Checkpoint**: Foundation ready. Invoice registration and matching stories can now be implemented.

---

## Phase 3: User Story 1 - Register Invoice Against A Purchase Order (Priority: P1) 🎯 MVP

**Goal**: Allow a finance agent to register one invoice against one vendor and one purchase order with duplicate protection and idempotent replay.

**Independent Test**: Register a valid invoice, verify a single persisted `PENDING` invoice is returned with `REQUEST_MATCH`, then verify duplicate reference rejection and same-key replay for the same semantic request.

### Tests for User Story 1 ⚠️

> **NOTE**: Write these tests first, ensure they fail before implementation.

- [x] T011 [P] [US1] Add contract coverage for POST /invoices success, `PENDING` state, next-action guidance, duplicate rejection, and idempotent replay in tests/contract/test_invoice_registration.py
- [x] T012 [P] [US1] Add integration coverage for invoice registration, vendor and purchase-order coherence, pending-state creation, and duplicate handling in tests/integration/test_invoice_registration.py

### Implementation for User Story 1

- [x] T013 [US1] Implement invoice registration service flow in src/domain/services/invoice_service.py
- [x] T014 [US1] Implement invoice creation and vendor and purchase-order coherence checks in src/persistence/repositories/invoice_repository.py and src/persistence/repositories/purchase_order_repository.py
- [x] T015 [US1] Implement POST /invoices request and response mapping with `PENDING` and `REQUEST_MATCH` semantics in src/api/routes/invoices.py and src/api/schemas/invoice.py

**Checkpoint**: User Story 1 is functional and independently testable.

---

## Phase 4: User Story 2 - Block Invoice Amounts Above Received Value (Priority: P1)

**Goal**: Reject invoice matches that exceed current receipt-backed value and return the exact shortfall with structured next-action guidance.

**Independent Test**: Match a registered invoice whose amount exceeds the linked purchase order's current received value and verify a `422` blocked response with exact shortfall, signed difference, line-level open exposure, and `WAIT_FOR_RECEIPT` or `CORRECT_INVOICE`.

### Tests for User Story 2 ⚠️

- [x] T016 [P] [US2] Add contract coverage for blocked POST /invoices/{invoiceId}/match outcomes, signed difference, open-line payloads, and conflicting idempotency reuse in tests/contract/test_invoice_matching.py
- [x] T017 [P] [US2] Add integration coverage for blocked match shortfall calculation, open-line exposure derivation, and next-action derivation in tests/integration/test_invoice_matching.py

### Implementation for User Story 2

- [x] T018 [US2] Implement blocked match evaluation and snapshot persistence in src/domain/services/invoice_matching_service.py and src/persistence/repositories/invoice_repository.py
- [x] T019 [US2] Implement `422` blocked match response mapping with signed difference and open-line details in src/api/routes/invoices.py and src/api/schemas/invoice.py
- [x] T020 [US2] Enforce match idempotency replay and invalid workflow rejection in src/domain/services/invoice_matching_service.py and src/core/idempotency.py

**Checkpoint**: User Stories 1 and 2 are functional and independently testable.

---

## Phase 5: User Story 3 - Warn On Partial Receipt Exposure Without Blocking (Priority: P2)

**Goal**: Return `202` matched-with-warning outcomes for partially received purchase orders and `200` clean matches once receipt exposure is fully closed.

**Independent Test**: Match a registered invoice that is supportable by current received value on a partially received purchase order and verify a `202` warning response with specific open lines and proceed-or-wait guidance, then re-match after additional receipts and verify a `200` clean response.

### Tests for User Story 3 ⚠️

- [x] T021 [P] [US3] Add contract coverage for `202` warning and `200` clean match outcomes including open-line details and next actions in tests/contract/test_invoice_matching.py
- [x] T022 [P] [US3] Add integration coverage for partial-receipt warning, exact-equality warning behavior, clean full-receipt match, and re-match-after-receipt in tests/integration/test_invoice_matching.py

### Implementation for User Story 3

- [x] T023 [US3] Implement warning and clean match outcomes plus invoice `last_match_outcome` updates in src/domain/services/invoice_matching_service.py and src/persistence/repositories/invoice_repository.py
- [x] T024 [US3] Implement warning payload, open-line exposure details, and clean success response variants in src/api/routes/invoices.py and src/api/schemas/invoice.py

**Checkpoint**: All three user stories are functional and independently testable.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Preserve existing features, update docs, and validate the full invoice flow.

- [x] T025 [P] Update vendor exposure aggregation for the expanded invoice status set in src/persistence/repositories/invoice_repository.py and tests/contract/test_vendor_exposure.py
- [x] T026 [P] Document invoice registration and matching behavior in specs/005-invoice-matching/quickstart.md and CHANGELOG.md
- [x] T027 Validate end-to-end invoice flows and align shared test fixtures in tests/conftest.py and src/persistence/seed/bootstrap.py

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies. Can start immediately.
- **Foundational (Phase 2)**: Depends on Setup completion. Blocks all user stories.
- **User Story 1 (Phase 3)**: Depends on Foundational completion.
- **User Story 2 (Phase 4)**: Depends on Foundational and User Story 1 because matching requires a registered invoice.
- **User Story 3 (Phase 5)**: Depends on Foundational and User Story 2 because it extends the same match workflow with success variants.
- **Polish (Phase 6)**: Depends on all desired user stories being complete.

### User Story Dependencies

- **US1**: No dependency on other user stories after Foundational.
- **US2**: Requires US1 registration flow so an invoice exists to match.
- **US3**: Requires US2 match flow so the warning and clean success outcomes extend the same endpoint and snapshot behavior.

### Within Each User Story

- Contract and integration tests must be written and fail before implementation.
- Persistence and domain models before services.
- Services before route and schema wiring.
- Route responses and error semantics before final story validation.

### Parallel Opportunities

- T002 and T003 can run in parallel during Setup.
- T005, T006, T008, and T009 can run in parallel during Foundational.
- T011 and T012 can run in parallel for US1.
- T016 and T017 can run in parallel for US2.
- T021 and T022 can run in parallel for US3.
- T025 and T026 can run in parallel during Polish.

---

## Parallel Example: User Story 1

```bash
# Launch User Story 1 tests together:
Task: "T011 Add contract coverage for POST /invoices success, duplicate rejection, and idempotent replay in tests/contract/test_invoice_registration.py"
Task: "T012 Add integration coverage for invoice registration, vendor and purchase-order coherence, and duplicate handling in tests/integration/test_invoice_registration.py"
```

## Parallel Example: User Story 2

```bash
# Launch User Story 2 tests together:
Task: "T016 Add contract coverage for blocked POST /invoices/{invoiceId}/match outcomes and conflicting idempotency reuse in tests/contract/test_invoice_matching.py"
Task: "T017 Add integration coverage for blocked match shortfall calculation and next-action derivation in tests/integration/test_invoice_matching.py"
```

## Parallel Example: User Story 3

```bash
# Launch User Story 3 tests together:
Task: "T021 Add contract coverage for 202 warning and 200 clean match outcomes in tests/contract/test_invoice_matching.py"
Task: "T022 Add integration coverage for partial-receipt warning, clean full-receipt match, and re-match-after-receipt in tests/integration/test_invoice_matching.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup.
2. Complete Phase 2: Foundational.
3. Complete Phase 3: User Story 1.
4. Stop and validate POST /invoices independently before moving to matching.

### Incremental Delivery

1. Finish Setup and Foundational to establish invoice persistence, errors, and route scaffolding.
2. Deliver US1 and validate invoice registration, duplicate rejection, and idempotent replay.
3. Deliver US2 and validate hard reject matching with exact shortfall and next action.
4. Deliver US3 and validate warning and clean match outcomes plus re-match behavior after additional receipts.
5. Finish Polish to preserve vendor exposure behavior and update docs.

### Parallel Team Strategy

1. One developer handles T005 and T006 while another handles T008 and T009 after Setup.
2. After Foundational completes, one developer can own contract tests while another owns integration tests inside each story phase.
3. Polish tasks T025 and T026 can run in parallel once story work is complete.

---

## Notes

- [P] tasks touch different files and can be executed in parallel once their dependencies are satisfied.
- User story labels map every story task back to the specification for traceability.
- Each story preserves machine-readable error semantics, correlation IDs, and idempotency behavior.
- Commit after each logical group of completed tasks.
