---
description: "Task list for MCP server tools implementation"
---

# Tasks: MCP Server Tools

**Input**: Design documents from `/specs/020-mcp-server-tools/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/mcp-server-tools.yaml, quickstart.md

**Tests**: Contract and integration tests are REQUIRED for this feature because it adds a new externally visible machine interface, changes discovery behavior, and must preserve idempotent replay plus structured error semantics.

**Organization**: Tasks are grouped by user story so each story can be implemented and validated independently once the shared MCP adapter foundation is ready.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel if the task touches different files and has no dependency on an unfinished task
- **[Story]**: User story label for story-phase tasks only
- Every task includes the exact file path it should change or validate

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Add the MCP dependency and feature scaffolding without changing business behavior yet.

- [ ] T001 Add the MCP Python SDK dependency in pyproject.toml
- [ ] T002 Create MCP adapter scaffolding in src/mcp/**init**.py, src/mcp/models.py, src/mcp/tools.py, and src/mcp/server.py
- [ ] T003 [P] Create MCP test scaffolding in tests/contract/test_mcp_tools.py, tests/integration/test_mcp_tools.py, and tests/unit/test_mcp_server.py

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Establish the shared MCP result models, session wiring, and adapter helpers used by all tool stories.

**⚠️ CRITICAL**: No user story work should begin until this phase is complete.

- [ ] T004 Define shared MCP invocation and result-envelope models in src/mcp/models.py
- [ ] T005 [P] Implement shared tool helper functions for correlation IDs, success envelopes, and service-error mapping in src/mcp/tools.py
- [ ] T006 [P] Build the mounted MCP server instance and tool registration surface in src/mcp/server.py
- [ ] T007 Mount the MCP server and session-manager lifecycle into src/main.py
- [ ] T008 [P] Add unit coverage for envelope mapping and correlation/idempotency validation helpers in tests/unit/test_mcp_server.py

**Checkpoint**: MCP server scaffolding, shared result envelopes, and app mounting are ready for story implementation.

---

## Phase 3: User Story 1 - Execute Core P2P Workflows Through MCP Tools (Priority: P1) 🎯 MVP

**Goal**: Let an MCP client execute the full purchase-to-pay workflow through tool calls that preserve the same business outcomes as the current REST API.

**Independent Test**: Connect to the mounted MCP server, execute purchase-order creation, submission, receiving, invoice creation, matching, approval, and payment in order, and verify each tool returns a structured success envelope containing the current REST-equivalent business payload.

### Tests for User Story 1 ⚠️

> **NOTE**: Write these tests first and ensure they fail before implementation.

- [ ] T009 [P] [US1] Add contract coverage for tool discovery and the mutating purchase-order plus invoice workflow tools in tests/contract/test_mcp_tools.py
- [ ] T010 [P] [US1] Add integration coverage for one end-to-end purchase-to-pay MCP tool flow in tests/integration/test_mcp_tools.py

### Implementation for User Story 1

- [ ] T011 [US1] Implement vendor and purchase-order MCP tools in src/mcp/tools.py using src/domain/services/vendor_eligibility_service.py, src/domain/services/purchase_order_service.py, and src/domain/services/goods_receipt_service.py
- [ ] T012 [US1] Implement invoice workflow MCP tools in src/mcp/tools.py using src/domain/services/invoice_service.py, src/domain/services/invoice_matching_service.py, src/domain/services/invoice_approval_service.py, and src/domain/services/invoice_payment_service.py
- [ ] T013 [US1] Register all P1 workflow tools with stable names and descriptions in src/mcp/server.py

**Checkpoint**: User Story 1 is functional and independently testable as the MVP slice.

---

## Phase 4: User Story 2 - Discover And Understand Available Tools (Priority: P2)

**Goal**: Let MCP clients inspect tool names, descriptions, and input contracts clearly enough to use the server without reading the REST implementation.

**Independent Test**: Connect to the MCP server, list tools, and verify the expected tool names, descriptions, and required input fields are present and stable.

### Tests for User Story 2 ⚠️

- [ ] T014 [P] [US2] Extend contract coverage for tool metadata, required arguments, and schema discoverability in tests/contract/test_mcp_tools.py

### Implementation for User Story 2

- [ ] T015 [US2] Refine tool docstrings, titles, and argument annotations for clear discovery in src/mcp/tools.py and src/mcp/server.py
- [ ] T016 [US2] Align contract examples and operator guidance with the implemented tool catalog in specs/020-mcp-server-tools/contracts/mcp-server-tools.yaml and specs/020-mcp-server-tools/quickstart.md

**Checkpoint**: User Story 2 is independently testable and makes the tool surface self-describing.

---

## Phase 5: User Story 3 - Preserve Deterministic Recovery Semantics Through MCP (Priority: P3)

**Goal**: Preserve idempotent replay, correlation propagation, and structured business failures through the MCP interface.

**Independent Test**: Replay at least one mutating tool with the same idempotency key and verify the same logical result is returned, then trigger at least one business failure and verify the MCP result preserves the current machine-readable error semantics.

### Tests for User Story 3 ⚠️

- [ ] T017 [P] [US3] Add contract coverage for required idempotency keys, replay behavior, and structured tool-error envelopes in tests/contract/test_mcp_tools.py
- [ ] T018 [P] [US3] Add integration coverage for replayed tool calls and business-failure propagation in tests/integration/test_mcp_tools.py

### Implementation for User Story 3

- [ ] T019 [US3] Enforce mutating-tool idempotency-key requirements and correlation-id echo behavior in src/mcp/models.py and src/mcp/tools.py
- [ ] T020 [US3] Map existing ServiceError results into structured MCP failure envelopes and error results in src/mcp/tools.py
- [ ] T021 [US3] Validate follow-up identifiers such as credit_check_id remain visible in MCP success payloads in src/mcp/tools.py and src/mcp/server.py

**Checkpoint**: User Story 3 is independently testable and preserves the repo's deterministic machine-first recovery semantics.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Finalize feature documentation, release notes, and regression validation for the full MCP slice.

- [ ] T022 [P] Update the MCP feature spec artifacts to reflect the implemented tool names and envelopes in specs/020-mcp-server-tools/plan.md, specs/020-mcp-server-tools/research.md, and specs/020-mcp-server-tools/data-model.md if implementation details require minor sync corrections
- [ ] T023 [P] Add the unreleased MCP tools entry in CHANGELOG.md
- [ ] T024 Run the targeted regression suite covering tests/contract/test_mcp_tools.py, tests/integration/test_mcp_tools.py, and tests/unit/test_mcp_server.py

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies. Can start immediately.
- **Foundational (Phase 2)**: Depends on Setup completion. Blocks all user stories.
- **User Story 1 (Phase 3)**: Depends on Foundational completion.
- **User Story 2 (Phase 4)**: Depends on User Story 1 because discovery should validate the implemented tool catalog.
- **User Story 3 (Phase 5)**: Depends on User Story 1 because replay and error preservation require working tool execution.
- **Polish (Phase 6)**: Depends on all desired user stories being complete.

### User Story Dependencies

- **US1**: No dependency on other stories after Foundational; this is the MVP.
- **US2**: Depends on US1 because tool metadata is meaningful only after the executable catalog exists.
- **US3**: Depends on US1 because deterministic replay and failure propagation must be exercised on implemented tools.

### Within Each User Story

- Contract and integration tests must be written and fail before implementation for MCP-facing behavior.
- Shared envelope and mounting helpers must exist before individual tool handlers depend on them.
- Tool registration should follow tool implementation so discovery tests reflect the final behavior.
- Validate each story independently before moving to the next priority.

### Parallel Opportunities

- **Setup**: T003 can run in parallel with T001 and T002 once file paths are known.
- **Foundational**: T005, T006, and T008 can run in parallel after T004 defines the shared model vocabulary.
- **US1**: T009 and T010 can run in parallel.
- **US3**: T017 and T018 can run in parallel.
- **Polish**: T022 and T023 can run in parallel before T024.

---

## Parallel Example: User Story 1

```text
Task: "T009 Add contract coverage for MCP tool discovery and the mutating purchase-order plus invoice workflow tools in tests/contract/test_mcp_tools.py"
Task: "T010 Add integration coverage for one end-to-end purchase-to-pay MCP tool flow in tests/integration/test_mcp_tools.py"
```

## Parallel Example: User Story 3

```text
Task: "T017 Add contract coverage for required idempotency keys, replay behavior, and structured tool-error envelopes in tests/contract/test_mcp_tools.py"
Task: "T018 Add integration coverage for replayed tool calls and business-failure propagation in tests/integration/test_mcp_tools.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup.
2. Complete Phase 2: Foundational.
3. Complete Phase 3: User Story 1.
4. Stop and validate the end-to-end MCP purchase-to-pay flow before expanding discovery and replay semantics.

### Incremental Delivery

1. Finish Setup and Foundational to establish the mounted MCP server and shared envelopes.
2. Deliver US1 and validate executable workflow tools.
3. Deliver US2 and validate tool discoverability.
4. Deliver US3 and validate replay plus failure semantics.
5. Finish Polish with docs, changelog, and targeted regression validation.

### Parallel Team Strategy

1. One lane adds shared MCP server plumbing while another prepares contract and integration tests.
2. After Foundational completes, one lane can focus on purchase-order tools while another focuses on invoice tools because both live in src/mcp/tools.py but rely on different underlying services.
3. Discovery polish and recovery semantics can be split after the basic executable tool surface is stable.

---

## Notes

- All tasks follow the required checklist format with exact file paths.
- Contract and integration tests are included because the MCP surface is a new external machine interface.
- The REST API remains authoritative; no task introduces duplicate business logic or persistence owned by the MCP layer.
