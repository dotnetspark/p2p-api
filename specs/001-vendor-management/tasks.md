---
description: "Task list for Vendor Management feature implementation"
---

# Tasks: Vendor Management

**Input**: Design documents from `/specs/001-vendor-management/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/vendor-management.openapi.yaml, quickstart.md

**Tests**: Contract and integration tests are REQUIRED for API-facing stories in this feature. Unit tests are included only where they protect the shared inactive-vendor rule.

**Organization**: Tasks are grouped by user story so each story can be implemented and validated independently.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Initialize the Python/FastAPI project skeleton and local tooling.

- [x] T001 Create Python project metadata and runtime dependencies in pyproject.toml
- [x] T002 Create package and test directory skeleton in src/**init**.py, src/api/**init**.py, src/domain/**init**.py, src/persistence/**init**.py, tests/**init**.py, tests/contract/**init**.py, tests/integration/**init**.py, and tests/unit/**init**.py
- [x] T003 [P] Create FastAPI application bootstrap in src/main.py
- [x] T004 [P] Create API router composition module in src/api/router.py
- [x] T005 [P] Create environment and settings loader for SQLite and app configuration in src/api/dependencies/settings.py

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Build shared persistence, error handling, request tracing, and seed-data infrastructure required by all stories.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [x] T006 Create SQLAlchemy engine, session factory, and declarative base in src/persistence/database.py
- [x] T007 [P] Create persistence vendor model in src/persistence/models/vendor.py
- [x] T008 [P] Create persistence invoice model in src/persistence/models/invoice.py
- [x] T009 [P] Create shared API schemas for correlation IDs and error envelopes in src/api/schemas/common.py and src/api/schemas/error.py
- [x] T010 Implement correlation ID middleware and exception translation in src/api/dependencies/request_context.py and src/api/dependencies/error_handlers.py
- [x] T011 Create vendor and invoice repositories in src/persistence/repositories/vendor_repository.py and src/persistence/repositories/invoice_repository.py
- [x] T012 Implement startup seed bootstrap for vendors and invoices in src/persistence/seed/bootstrap.py
- [x] T013 Implement shared vendor domain model and inactive-vendor rule in src/domain/models/vendor.py and src/domain/rules/vendor_eligibility.py
- [x] T014 Create pytest fixtures and SQLite integration harness in tests/conftest.py

**Checkpoint**: Shared infrastructure is ready; user stories can now proceed.

---

## Phase 3: User Story 1 - Confirm Vendor Eligibility (Priority: P1) 🎯 MVP

**Goal**: Let procurement agents determine whether a vendor exists and is currently eligible for new obligations.

**Independent Test**: Request vendor eligibility for one active vendor and one inactive vendor and confirm the response clearly indicates whether obligations may proceed.

### Tests for User Story 1

- [x] T015 [P] [US1] Create contract test for GET /vendors/{vendorId}/eligibility in tests/contract/test_vendor_eligibility.py
- [x] T016 [P] [US1] Create integration test for active, inactive, and missing vendor eligibility scenarios in tests/integration/test_vendor_eligibility.py

### Implementation for User Story 1

- [x] T017 [P] [US1] Create vendor eligibility response schema in src/api/schemas/vendor_eligibility.py
- [x] T018 [US1] Implement vendor eligibility service in src/domain/services/vendor_eligibility_service.py
- [x] T019 [US1] Implement vendor eligibility route in src/api/routes/vendor_eligibility.py
- [x] T020 [US1] Register the vendor eligibility route in src/api/router.py and src/main.py

**Checkpoint**: User Story 1 is independently functional and testable.

---

## Phase 4: User Story 2 - Block Inactive Vendor Obligations (Priority: P1)

**Goal**: Enforce the inactive-vendor rule in reusable domain logic so downstream obligation-creation flows cannot create or partially create invalid commitments.

**Independent Test**: Execute the shared obligation guard for active and inactive vendors and confirm inactive vendors are rejected with the stable `VENDOR_INACTIVE` result before any obligation write step proceeds.

### Tests for User Story 2

- [x] T021 [P] [US2] Create unit test for inactive-vendor guard outcomes in tests/unit/test_obligation_guard_service.py
- [x] T022 [P] [US2] Create integration test for stale-status reevaluation with seeded vendors in tests/integration/test_obligation_guard_service.py

### Implementation for User Story 2

- [x] T023 [P] [US2] Create obligation guard command and result models in src/domain/models/obligation_guard.py
- [x] T024 [US2] Implement obligation guard service with stable `VENDOR_INACTIVE` handling in src/domain/services/obligation_guard_service.py
- [x] T025 [US2] Expose the shared inactive-vendor rule for downstream mutating flows in src/domain/rules/vendor_eligibility.py and src/domain/services/obligation_guard_service.py

**Checkpoint**: User Story 2 is independently functional and testable.

---

## Phase 5: User Story 3 - Review Vendor Outstanding Obligations (Priority: P2)

**Goal**: Let finance agents retrieve a server-computed AP exposure summary for a vendor without performing any arithmetic client-side.

**Independent Test**: Request vendor exposure for a vendor with unpaid invoices and another with no unpaid invoices and confirm the totals and counts match the seeded invoice data.

### Tests for User Story 3

- [x] T026 [P] [US3] Create contract test for GET /vendors/{vendorId}/exposure in tests/contract/test_vendor_exposure.py
- [x] T027 [P] [US3] Create integration test for exposure totals, zero exposure, and missing vendor scenarios in tests/integration/test_vendor_exposure.py

### Implementation for User Story 3

- [x] T028 [P] [US3] Create vendor exposure response schema in src/api/schemas/vendor_exposure.py
- [x] T029 [US3] Implement invoice exposure aggregation query in src/persistence/repositories/invoice_repository.py
- [x] T030 [US3] Implement vendor exposure service in src/domain/services/vendor_exposure_service.py
- [x] T031 [US3] Implement vendor exposure route in src/api/routes/vendor_exposure.py
- [x] T032 [US3] Register the vendor exposure route in src/api/router.py and src/main.py

**Checkpoint**: User Story 3 is independently functional and testable.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Finish cross-story documentation, validation, and observability details.

- [x] T033 [P] Add API usage examples and seed-data assumptions to specs/001-vendor-management/quickstart.md
- [x] T034 [P] Align correlation ID and error examples with implementation details in specs/001-vendor-management/contracts/vendor-management.openapi.yaml
- [x] T035 Validate the end-to-end quickstart scenarios and record any final corrections in specs/001-vendor-management/quickstart.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1: Setup** has no dependencies and can start immediately.
- **Phase 2: Foundational** depends on Phase 1 and blocks all story work.
- **Phase 3: US1** depends on Phase 2.
- **Phase 4: US2** depends on Phase 2 and can run in parallel with US1 after the shared vendor rule exists.
- **Phase 5: US3** depends on Phase 2 and can start after repository and seed infrastructure are in place.
- **Phase 6: Polish** depends on the stories you want to ship being complete.

### User Story Dependencies

- **US1**: No dependency on other user stories after Foundational.
- **US2**: No dependency on US1; it reuses the shared vendor rule from Phase 2.
- **US3**: No dependency on US1 or US2 after Foundational, though it reuses the shared repository and tracing infrastructure.

### Within Each User Story

- Contract and integration tests must be written before implementation for API stories.
- Domain or response models come before services.
- Services come before routes.
- Route registration follows route implementation.

### Suggested Completion Order

1. Setup
2. Foundational
3. US1 as the MVP slice
4. US2 to harden the inactive-vendor business invariant
5. US3 to add finance exposure visibility
6. Polish

---

## Parallel Opportunities

- T003, T004, and T005 can run in parallel once T001 and T002 are complete.
- T007, T008, and T009 can run in parallel after T006.
- T015 and T016 can run in parallel for US1.
- T021 and T022 can run in parallel for US2.
- T026 and T027 can run in parallel for US3.
- T033 and T034 can run in parallel during Polish.

### Parallel Example: User Story 1

```text
T015 tests/contract/test_vendor_eligibility.py
T016 tests/integration/test_vendor_eligibility.py
T017 src/api/schemas/vendor_eligibility.py
```

### Parallel Example: User Story 3

```text
T026 tests/contract/test_vendor_exposure.py
T027 tests/integration/test_vendor_exposure.py
T028 src/api/schemas/vendor_exposure.py
```

---

## Implementation Strategy

### MVP First

1. Complete Phase 1: Setup.
2. Complete Phase 2: Foundational.
3. Complete Phase 3: User Story 1.
4. Validate the eligibility contract and seeded-vendor scenarios before moving on.

### Incremental Delivery

1. Deliver US1 so procurement agents can plan safely.
2. Deliver US2 so downstream write flows can reuse the stable inactive-vendor guard.
3. Deliver US3 so finance agents can assess exposure before invoice approval.

### Parallel Team Strategy

1. One developer completes Setup and Foundational.
2. After Phase 2, one developer can take US1 while another takes US2 or US3.
3. Merge on the shared error semantics and correlation ID behavior before Polish.

---

## Notes

- All tasks follow the required checklist format with task IDs, optional parallel markers, story labels where required, and explicit file paths.
- Contract and integration tests are included for both API-facing stories because they change externally visible behavior.
- US2 includes focused guard-service tests because it defines reusable business invariants for later mutating features.
