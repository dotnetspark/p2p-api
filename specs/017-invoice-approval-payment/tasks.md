---
description: "Task list for invoice approval and payment implementation"
---

# Tasks: Invoice Approval and Payment

**Input**: Design documents from `/specs/017-invoice-approval-payment/`

**Prerequisites**: plan.md, spec.md, enhancement.md, research.md, data-model.md, contracts/invoice-approval-payment.openapi.yaml, quickstart.md

**Tests**: Contract and integration tests are REQUIRED for both user stories because they add externally visible API operations, lifecycle transitions, and machine-readable error semantics.

**Organization**: Tasks are grouped by user story so each story can be implemented and validated independently once prerequisites are complete.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel if the task touches different files and has no dependency on an unfinished task
- **[Story]**: User story label for story-phase tasks only
- Every task includes the exact file path it should change or validate

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Capture the schema-governance decision required before implementation changes introduce new fields, statuses, and entities.

- [X] T001 Add the schema change ADR for invoice approval, payment, and GL entry persistence in docs/adr/017-invoice-approval-payment-schema.md

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Establish the shared domain, persistence, error, and schema infrastructure used by both approval and payment.

**⚠️ CRITICAL**: No user story work should begin until this phase is complete.

- [X] T002 Extend invoice lifecycle states, approval/payment result dataclasses, and transition helpers in src/domain/models/invoice.py
- [X] T003 [P] Add purchase-order close-on-payment transition logic in src/domain/models/purchase_order.py
- [X] T004 [P] Add approved_at and paid_at persistence columns to src/persistence/models/invoice.py
- [X] T005 [P] Create the GL entry ORM model in src/persistence/models/gl_entry.py
- [X] T006 Implement GL entry persistence access in src/persistence/repositories/gl_entry_repository.py
- [X] T007 Extend invoice persistence and idempotent replay lookups for approval/payment in src/persistence/repositories/invoice_repository.py
- [X] T008 [P] Extend purchase order persistence to support payment-triggered closure in src/persistence/repositories/purchase_order_repository.py
- [X] T009 [P] Add approval/payment service error helpers and machine-readable codes in src/core/errors.py
- [X] T010 [P] Add approval and payment request/response schema models in src/api/schemas/invoice.py

**Checkpoint**: Shared lifecycle, persistence, and API primitives exist for both stories.

---

## Phase 3: User Story 1 - Approve Matched Invoice (Priority: P1) 🎯 MVP

**Goal**: Allow a matched invoice to be approved exactly once per logical request and generate two balanced GL entries.

**Independent Test**: Approve a matched invoice through `POST /invoices/{invoice_id}/approve` and verify the invoice becomes `APPROVED`, exactly two balanced GL entries are returned, invalid-state approval is rejected, and idempotent replay does not duplicate entries.

### Tests for User Story 1

- [X] T011 [P] [US1] Add contract coverage for `POST /invoices/{invoice_id}/approve` in tests/contract/test_invoice_approval.py
- [X] T012 [P] [US1] Add approval workflow integration coverage in tests/integration/test_invoice_approval.py

### Implementation for User Story 1

- [X] T013 [P] [US1] Create the hardcoded vendor-category expense account map and balanced GL builders in src/domain/rules/gl_posting.py
- [X] T014 [US1] Implement idempotent invoice approval orchestration in src/domain/services/invoice_approval_service.py
- [X] T015 [US1] Persist invoice approval transitions and generated GL rows in src/persistence/repositories/invoice_repository.py and src/persistence/repositories/gl_entry_repository.py
- [X] T016 [US1] Expose `POST /invoices/{invoice_id}/approve` and approval response serialization in src/api/routes/invoices.py and src/api/schemas/invoice.py

**Checkpoint**: User Story 1 is fully functional and can be validated independently as the MVP slice.

---

## Phase 4: User Story 2 - Pay Approved Invoice and Close Purchase Order (Priority: P2)

**Goal**: Allow an approved invoice to be marked paid exactly once per logical request and automatically close the linked purchase order.

**Independent Test**: Mark an approved invoice paid through `POST /invoices/{invoice_id}/pay` and verify the invoice becomes `PAID`, the linked purchase order becomes `CLOSED`, invalid pre-approval payment is rejected, and idempotent replay does not duplicate the transition.

### Tests for User Story 2

- [X] T017 [P] [US2] Add contract coverage for `POST /invoices/{invoice_id}/pay` in tests/contract/test_invoice_payment.py
- [X] T018 [P] [US2] Add payment and purchase-order-closure integration coverage in tests/integration/test_invoice_payment.py

### Implementation for User Story 2

- [X] T019 [US2] Implement idempotent invoice payment orchestration in src/domain/services/invoice_payment_service.py
- [X] T020 [US2] Persist payment timestamps and payment-triggered purchase-order closure in src/persistence/repositories/invoice_repository.py and src/persistence/repositories/purchase_order_repository.py
- [X] T021 [US2] Expose `POST /invoices/{invoice_id}/pay` and payment response serialization in src/api/routes/invoices.py and src/api/schemas/invoice.py

**Checkpoint**: User Story 2 is independently testable and completes the post-match invoice lifecycle.

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Finalize the feature contract, enhancement notes, operator guidance, release notes, and validation pass.

- [X] T022 [P] Update approval/payment examples and recovery semantics in specs/017-invoice-approval-payment/contracts/invoice-approval-payment.openapi.yaml
- [X] T023 [P] Update original-request versus repo-deviation notes in specs/017-invoice-approval-payment/enhancement.md
- [X] T024 [P] Update execution and verification guidance in specs/017-invoice-approval-payment/quickstart.md
- [X] T025 Update the unreleased feature entry in CHANGELOG.md
- [X] T026 Run the targeted regression suite covering tests/contract/test_invoice_approval.py, tests/contract/test_invoice_payment.py, tests/integration/test_invoice_approval.py, and tests/integration/test_invoice_payment.py

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Starts immediately.
- **Foundational (Phase 2)**: Depends on Phase 1 and blocks all story work.
- **User Story 1 (Phase 3)**: Depends on Phase 2.
- **User Story 2 (Phase 4)**: Depends on Phase 2 and reuses lifecycle/status work completed for User Story 1.
- **Polish (Phase 5)**: Depends on the user stories you intend to ship.

### User Story Dependencies

- **US1**: No dependency on later stories; this is the MVP.
- **US2**: Depends on the shared lifecycle foundation and assumes an `APPROVED` invoice state exists, so it should follow US1 in delivery order.

### Within Each User Story

- Write contract and integration tests first, and confirm they fail before implementation.
- Complete domain and rule logic before route wiring.
- Complete persistence changes before relying on replayed API outcomes.
- Validate each story independently before moving to the next priority.

### Parallel Opportunities

- **Foundational**: T003, T004, T005, T008, T009, and T010 can proceed in parallel after T002 starts the shared lifecycle vocabulary.
- **US1**: T011, T012, and T013 can run in parallel.
- **US2**: T017 and T018 can run in parallel before T019.
- **Polish**: T022, T023, and T024 can run in parallel.

---

## Parallel Example: User Story 1

```text
Task: "Add contract coverage for POST /invoices/{invoice_id}/approve in tests/contract/test_invoice_approval.py"
Task: "Add approval workflow integration coverage in tests/integration/test_invoice_approval.py"
Task: "Create the hardcoded vendor-category expense account map and balanced GL builders in src/domain/rules/gl_posting.py"
```

## Parallel Example: User Story 2

```text
Task: "Add contract coverage for POST /invoices/{invoice_id}/pay in tests/contract/test_invoice_payment.py"
Task: "Add payment and purchase-order-closure integration coverage in tests/integration/test_invoice_payment.py"
```

---

## Implementation Strategy

### MVP First

1. Complete Phase 1.
2. Complete Phase 2.
3. Complete Phase 3.
4. Validate approval end to end before moving on.

### Incremental Delivery

1. Ship the approval workflow first as the assignment-aligned MVP.
2. Add payment and PO closure as the next incremental slice.
3. Finish with contract, quickstart, changelog, and regression validation updates.

### Parallel Team Strategy

1. One developer completes the shared lifecycle and persistence foundation.
2. Once Phase 2 is done, one lane can execute US1 tests while another prepares the GL posting rule file.
3. After US1 stabilizes, US2 can proceed with separate contract and integration coverage in parallel.

---

## Notes

- All tasks follow the required checklist format: checkbox, task ID, optional `[P]`, required story label for story phases, and exact file paths.
- Contract and integration tests are included because this feature adds new API endpoints and externally visible lifecycle semantics.
- The schema ADR is included up front to satisfy the repository constitution before implementation changes add new statuses, timestamps, and the `GLEntry` entity.
