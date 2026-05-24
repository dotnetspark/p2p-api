# Tasks: Purchase Order Lifecycle

**Input**: Design documents from `/specs/004-po-lifecycle/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: Contract and integration tests are REQUIRED for each user story because this feature adds new externally visible API behavior, workflow transitions, and machine-consumable error semantics.

**Organization**: Tasks are grouped by user story so each increment can be implemented and validated in business-priority order while preserving real workflow dependencies between stories and the repo's existing API -> domain -> persistence layering.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create the purchase-order feature file structure inside the existing layered FastAPI service.

- [x] T001 Create purchase-order route module in src/api/routes/purchase_orders.py
- [x] T002 [P] Create purchase-order schema module in src/api/schemas/purchase_order.py
- [x] T003 [P] Create purchase-order domain aggregate module in src/domain/models/purchase_order.py
- [x] T004 [P] Create goods-receipt domain model module in src/domain/models/goods_receipt.py
- [x] T005 [P] Create purchase-order persistence model module in src/persistence/models/purchase_order.py
- [x] T006 [P] Create goods-receipt persistence model module in src/persistence/models/goods_receipt.py

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Establish shared persistence, services, routing, and error semantics required by every purchase-order story without introducing cross-layer dependency violations.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [x] T007 Create purchase-order repository in src/persistence/repositories/purchase_order_repository.py with no imports from src/api
- [x] T008 [P] Create goods-receipt repository in src/persistence/repositories/goods_receipt_repository.py
- [x] T009 [P] Create purchase-order service in src/domain/services/purchase_order_service.py using only src/domain and src/core dependencies
- [x] T010 [P] Create goods-receipt service in src/domain/services/goods_receipt_service.py using only src/domain and src/core dependencies
- [x] T011 Extend persistence setup for purchase orders and receipts in src/persistence/database.py and src/persistence/seed/bootstrap.py
- [x] T012 [P] Extend shared purchase-order error catalog in src/core/errors.py for typed business and infrastructure outcomes consumed by all layers
- [x] T013 Register purchase-order routes in src/api/router.py and src/api/routes/purchase_orders.py while keeping HTTP request and response mapping isolated to src/api

**Checkpoint**: Shared purchase-order infrastructure is ready for story implementation.

---

## Phase 3: User Story 1 - Create Draft Purchase Orders (Priority: P1) 🎯 MVP

**Goal**: Allow procurement agents to create draft purchase orders for active vendors with validated line items.

**Independent Test**: Create a purchase order for an active vendor and verify the stored order starts in `DRAFT`; reject inactive vendors and invalid line inputs.

### Tests for User Story 1 ⚠️

- [x] T014 [P] [US1] Add contract tests for POST /purchase-orders in tests/contract/test_purchase_order_creation.py
- [x] T015 [P] [US1] Add integration tests for draft purchase-order creation in tests/integration/test_purchase_order_creation.py

### Implementation for User Story 1

- [x] T016 [US1] Implement draft purchase-order entity and line validation in src/domain/models/purchase_order.py
- [x] T017 [US1] Implement purchase-order ORM mappings for draft orders and lines in src/persistence/models/purchase_order.py
- [x] T018 [US1] Implement draft purchase-order creation workflow in src/persistence/repositories/purchase_order_repository.py and src/domain/services/purchase_order_service.py without importing API types into the domain layer
- [x] T019 [US1] Implement POST /purchase-orders request and response handling in src/api/routes/purchase_orders.py and src/api/schemas/purchase_order.py by translating typed service outcomes only at the API boundary

**Checkpoint**: User Story 1 is fully functional and independently testable.

---

## Phase 4: User Story 2 - Submit Draft Purchase Orders (Priority: P1)

**Goal**: Allow procurement agents to submit draft purchase orders and make them eligible for receiving.

**Independent Test**: Submit a draft purchase order and verify it transitions to `SUBMITTED`; reject submission attempts from any non-draft state.

### Tests for User Story 2 ⚠️

- [x] T020 [P] [US2] Add contract tests for POST /purchase-orders/{purchaseOrderId}/submit in tests/contract/test_purchase_order_submission.py
- [x] T021 [P] [US2] Add integration tests for purchase-order submission in tests/integration/test_purchase_order_submission.py

### Implementation for User Story 2

- [x] T022 [US2] Implement purchase-order submission state rules in src/domain/models/purchase_order.py and src/domain/services/purchase_order_service.py
- [x] T023 [US2] Implement idempotent submission persistence in src/persistence/repositories/purchase_order_repository.py without leaking persistence concerns into src/domain/services/purchase_order_service.py
- [x] T024 [US2] Implement POST /purchase-orders/{purchaseOrderId}/submit in src/api/routes/purchase_orders.py and src/api/schemas/purchase_order.py with API-only HTTP translation of invalid-state errors

**Checkpoint**: User Stories 1 and 2 both work, and submission is independently testable on a draft order fixture.

---

## Phase 5: User Story 3 - Record Partial Goods Receipts (Priority: P1)

**Goal**: Allow warehouse agents to record additive partial receipts without permitting over-receipt or receiving against unsubmitted orders.

**Independent Test**: Record a partial receipt, record a later receipt for the same line, verify cumulative totals increase correctly, and reject over-receipt and draft-order receiving.

### Tests for User Story 3 ⚠️

- [x] T025 [P] [US3] Add contract tests for POST /purchase-orders/{purchaseOrderId}/receive in tests/contract/test_purchase_order_receiving.py
- [x] T026 [P] [US3] Add integration tests for additive goods receipts in tests/integration/test_purchase_order_receiving.py

### Implementation for User Story 3

- [x] T027 [US3] Implement additive goods-receipt rules in src/domain/models/goods_receipt.py and src/domain/models/purchase_order.py
- [x] T028 [US3] Implement goods-receipt ORM mappings and persistence in src/persistence/models/goods_receipt.py and src/persistence/repositories/goods_receipt_repository.py
- [x] T029 [US3] Implement goods-receipt workflow with over-receipt protection in src/domain/services/goods_receipt_service.py and src/persistence/repositories/purchase_order_repository.py while preserving additive qty_received semantics
- [x] T030 [US3] Implement POST /purchase-orders/{purchaseOrderId}/receive in src/api/routes/purchase_orders.py and src/api/schemas/purchase_order.py with API-only translation of not-submitted and over-receipt errors

**Checkpoint**: User Stories 1 through 3 support draft creation, submission, and additive receipt accumulation.

---

## Phase 6: User Story 4 - Query Order State And Receipt Progress (Priority: P2)

**Goal**: Allow procurement agents to retrieve a full purchase-order view with cumulative line progress and receipt history.

**Independent Test**: Query a purchase order after multiple receipts and verify the response reports order status plus ordered, received, and remaining quantities for each line.

### Tests for User Story 4 ⚠️

- [x] T031 [P] [US4] Add contract tests for GET /purchase-orders/{purchaseOrderId} in tests/contract/test_purchase_order_query.py
- [x] T032 [P] [US4] Add integration tests for purchase-order state queries in tests/integration/test_purchase_order_query.py

### Implementation for User Story 4

- [x] T033 [US4] Implement purchase-order progress projection in src/domain/models/purchase_order.py and src/domain/services/purchase_order_service.py
- [x] T034 [US4] Implement query aggregation for orders and receipts in src/persistence/repositories/purchase_order_repository.py and src/persistence/repositories/goods_receipt_repository.py while preserving the future one-invoice-per-order boundary without implementing invoice behavior
- [x] T035 [US4] Implement GET /purchase-orders/{purchaseOrderId} response handling in src/api/routes/purchase_orders.py and src/api/schemas/purchase_order.py including DRAFT, SUBMITTED, and RECEIVED reporting while leaving CLOSED transition behavior unimplemented

**Checkpoint**: All four user stories are functional, and an agent can assess invoicing readiness from one query.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Finalize cross-story validation, documentation alignment, and regression coverage.

- [x] T036 [P] Align quickstart scenarios with implemented purchase-order workflow in specs/004-po-lifecycle/quickstart.md
- [x] T037 [P] Finalize purchase-order contract examples and error descriptions in specs/004-po-lifecycle/contracts/purchase-order-lifecycle.openapi.yaml
- [x] T038 Verify end-to-end purchase-order regression coverage in tests/contract/test_purchase_order_creation.py, tests/contract/test_purchase_order_submission.py, tests/contract/test_purchase_order_receiving.py, tests/contract/test_purchase_order_query.py, tests/integration/test_purchase_order_creation.py, tests/integration/test_purchase_order_submission.py, tests/integration/test_purchase_order_receiving.py, and tests/integration/test_purchase_order_query.py
- [x] T039 Verify implementation alignment with specs/004-po-lifecycle/spec.md and specs/004-po-lifecycle/enhancement.md, including additive receipts, deferred CLOSED transition, and one-invoice-per-order future compatibility

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies; start immediately.
- **Foundational (Phase 2)**: Depends on Setup completion and blocks all story work.
- **User Story 1 (Phase 3)**: Starts after Foundational completion.
- **User Story 2 (Phase 4)**: Depends on User Story 1 because submission requires draft purchase orders.
- **User Story 3 (Phase 5)**: Depends on User Story 2 because receiving requires submitted purchase orders.
- **User Story 4 (Phase 6)**: Depends on User Story 3 because the query story must expose receipt progress and history.
- **Polish (Phase 7)**: Depends on all targeted user stories being complete.

### User Story Dependencies

- **US1**: No story dependency after Foundational completion.
- **US2**: Depends on US1 domain, persistence, and API support for draft orders.
- **US3**: Depends on US1 and US2 because additive receipts are recorded against submitted orders.
- **US4**: Depends on US1 and US3 because the query view must summarize stored order and receipt progress.

### Within Each User Story

- Contract and integration tests must be written and fail before implementation.
- Domain rules before persistence workflow wiring.
- Persistence and services before endpoint handling.
- Endpoint and schema work before the story checkpoint is considered complete.
- No task should introduce imports from src/api into src/domain or src/persistence, or imports from src/persistence into src/api routes beyond the existing dependency injection boundary.

### Parallel Opportunities

- Phase 1 tasks marked `[P]` can run in parallel after T001 establishes the route module target.
- Phase 2 tasks T008, T009, T010, and T012 can run in parallel after repository and service targets are created.
- Contract and integration tests within each story can run in parallel.
- Story implementation tasks that touch different files within a story can run in parallel only where marked `[P]`; cross-story parallelism is limited by the real workflow dependencies above.

---

## Parallel Example: User Story 3

```text
Task: "Add contract tests for POST /purchase-orders/{purchaseOrderId}/receive in tests/contract/test_purchase_order_receiving.py"
Task: "Add integration tests for additive goods receipts in tests/integration/test_purchase_order_receiving.py"

Task: "Implement additive goods-receipt rules in src/domain/models/goods_receipt.py and src/domain/models/purchase_order.py"
Task: "Implement goods-receipt ORM mappings and persistence in src/persistence/models/goods_receipt.py and src/persistence/repositories/goods_receipt_repository.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup.
2. Complete Phase 2: Foundational.
3. Complete Phase 3: User Story 1.
4. Stop and validate draft purchase-order creation before moving on.

### Incremental Delivery

1. Deliver US1 to establish valid draft purchase orders.
2. Deliver US2 to make purchase orders eligible for fulfilment.
3. Deliver US3 to add additive receipt accumulation and receipt protections.
4. Deliver US4 to expose a machine-readable order-state view for invoicing decisions.
5. Finish with Phase 7 to align docs and regression coverage.

### Parallel Team Strategy

1. Complete Setup and Foundational work together.
2. Parallelize only the `[P]` tasks within the active phase.
3. Move to the next story only after the current story checkpoint passes, because the purchase-order lifecycle is sequential by design.

---

## Notes

- All tasks follow the required checklist format: checkbox, task ID, optional `[P]`, optional story label, and exact file path.
- `CLOSED` remains modeled in the design but is intentionally not implemented in this feature.
- The one-invoice-per-purchase-order rule is preserved as a later lifecycle boundary and should not trigger invoice work in these tasks.
- Original-assignment alignment must be maintained except for the intentional deviations documented in specs/004-po-lifecycle/enhancement.md.
- Additive receipt accumulation is a non-negotiable invariant for any task touching `qty_received` behavior.
