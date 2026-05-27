# Feature Specification: MCP Server Tools

**Feature Branch**: `feat/039-mcp-server-tools`

**Created**: 2026-05-26

**Status**: Draft

**Input**: User description: "Expose the existing P2P API as agent-callable tools through an MCP server, keeping the REST API as the system of record and treating LangGraph as one possible consumer rather than the primary integration model."

## User Scenarios & Testing _(mandatory)_

### User Story 1 - Execute Core P2P Workflows Through MCP Tools (Priority: P1)

As an agent runtime, I want to call the P2P workflow through MCP tools so that I can create purchase orders, register invoices, match invoices, approve invoices, and pay invoices without writing HTTP-specific integration code.

**Why this priority**: This is the core value of the feature. Without a usable MCP tool surface over the existing API, the repository remains machine-friendly only for direct HTTP callers.

**Independent Test**: Can be fully tested by invoking MCP tools for at least one end-to-end purchase-to-pay flow and verifying that each tool returns machine-usable success data or structured failure details derived from the underlying API behavior.

**Acceptance Scenarios**:

1. **Given** the MCP server is running, **When** an agent calls the tool for creating a purchase order with valid vendor and line-item data, **Then** the MCP server returns the created purchase-order result in a machine-usable structure.
2. **Given** the MCP server is running, **When** an agent calls the tools for invoice creation, matching, approval, and payment in the valid lifecycle order, **Then** the MCP server returns the same business outcomes that the underlying API would produce.
3. **Given** a workflow call fails for a business reason, **When** the MCP tool returns the result, **Then** the error remains machine-readable and preserves enough context for the agent to decide the next step.

---

### User Story 2 - Discover And Understand Available Tools (Priority: P2)

As an agent runtime, I want the MCP server to describe its available tools clearly so that I can select the right operation, provide the right inputs, and understand what outcome to expect.

**Why this priority**: Tool discovery is required for general MCP clients. A thin tool wrapper that hides parameters or outcome meaning would weaken the machine-first design already present in the API.

**Independent Test**: Can be fully tested by connecting to the MCP server, listing tools, and verifying that tool names, descriptions, and input schemas are sufficient to drive valid calls without reading the REST source code.

**Acceptance Scenarios**:

1. **Given** an MCP-compatible client connects to the server, **When** it lists available tools, **Then** it sees the P2P workflow operations with stable names and clear descriptions.
2. **Given** an MCP-compatible client inspects a tool schema, **When** it reviews the input contract, **Then** the required arguments and expected shapes are explicit enough to construct a valid request.
3. **Given** the tool wraps an operation with state or retry implications, **When** the client reviews its description or output schema, **Then** the retry, state, and next-step semantics are still understandable without reverse-engineering the API.

---

### User Story 3 - Preserve Deterministic Recovery Semantics Through MCP (Priority: P3)

As an agent runtime, I want MCP tool calls to preserve idempotency, correlation, and retry guidance so that moving from raw HTTP calls to tools does not make recovery behavior less deterministic.

**Why this priority**: The repository's machine-first value depends on deterministic recovery. The MCP layer must not hide idempotency or collapse business and infrastructure failures into opaque tool errors.

**Independent Test**: Can be fully tested by replaying at least one mutating MCP tool call with the same idempotency key and verifying that the tool returns the same logical outcome, plus by inducing a business failure and confirming the MCP result preserves structured error meaning.

**Acceptance Scenarios**:

1. **Given** an MCP tool wraps a mutating API call, **When** the same semantic request is replayed with the same idempotency key, **Then** the MCP tool returns the original logical outcome rather than duplicating the side effect.
2. **Given** the underlying API returns a structured business error, **When** the tool call fails, **Then** the MCP result preserves the error code, retryability, and actionable message.
3. **Given** the underlying API uses correlation identifiers and follow-up handles such as `credit_check_id`, **When** the MCP tool returns a result, **Then** those identifiers remain visible to the caller.

### Edge Cases

- What happens when an MCP client calls a mutating tool without supplying an idempotency key?
- How does the MCP layer represent underlying API business errors versus transient infrastructure failures?
- What happens when the MCP server and HTTP API disagree about required inputs or response fields?
- How does the MCP server handle tools whose workflow depends on follow-up reads such as vendor exposure or credit-check status?
- What happens when a client retries a tool call after a partial network failure and needs to determine whether the original operation completed?

## Requirements _(mandatory)_

### Functional Requirements

- **FR-001**: The system MUST expose the existing purchase-order, invoice, vendor-exposure, and credit-check workflows as MCP-callable tools.
- **FR-002**: The system MUST keep the existing REST API as the system of record for business behavior rather than re-implementing workflow logic in the MCP layer.
- **FR-003**: The system MUST provide stable MCP tool names for the supported workflow operations.
- **FR-004**: The system MUST define input schemas for each MCP tool so callers can construct valid requests without reading source code.
- **FR-005**: The system MUST return tool outputs that preserve the business meaning of the underlying API response rather than collapsing them into opaque strings.
- **FR-006**: The system MUST support mutating MCP tool calls for purchase-order creation, purchase-order submission, goods receipt recording, invoice creation, invoice matching, invoice approval, and invoice payment.
- **FR-007**: The system MUST support read-oriented MCP tool calls for purchase-order detail, vendor exposure, and credit-check status.
- **FR-008**: The system MUST preserve idempotency support for mutating workflows by allowing the caller to provide an idempotency key through the MCP interface.
- **FR-009**: The system MUST preserve correlation identifiers or equivalent trace data through MCP tool execution.
- **FR-010**: The system MUST preserve structured business error codes, retryability, and recovery guidance from the underlying API.
- **FR-011**: The system MUST not change the existing REST API contract to satisfy the MCP feature.
- **FR-012**: The MCP feature MUST be general-purpose enough that LangGraph can consume it, but it MUST not be modeled as LangGraph-specific integration.
- **FR-013**: The system MUST document the available MCP tools and how they map to the underlying workflow operations.

### API Contract & Recovery Requirements _(mandatory for APIs)_

- Define the exact MCP tool names, input shapes, and output shapes for each supported workflow operation.
- Define how idempotency keys, correlation identifiers, and follow-up handles such as `credit_check_id` are passed through the MCP layer.
- Define how the MCP server represents business failures, retryable infrastructure failures, and validation errors without losing machine-readable semantics.
- Define how the MCP layer surfaces underlying workflow states, next actions, and deterministic replay outcomes.

### Key Entities _(include if feature involves data)_

- **MCP Tool**: A callable operation that maps an agent request onto one existing P2P workflow capability and returns a machine-usable result.
- **Tool Invocation Context**: The caller-supplied metadata, such as idempotency key and correlation identifier, that preserves deterministic behavior and traceability.
- **Tool Result Envelope**: The structured success or failure output returned from an MCP tool call, including business data, errors, and follow-up identifiers.

## Success Criteria _(mandatory)_

### Measurable Outcomes

- **SC-001**: Agents can complete at least one full purchase-to-pay workflow through MCP tools without issuing raw HTTP calls directly.
- **SC-002**: For supported mutating workflows, 100% of tested MCP retries with the same idempotency key replay the original logical outcome instead of creating duplicate side effects.
- **SC-003**: For supported business failures, 100% of tested MCP tool errors preserve a machine-readable code and retryability signal that matches the underlying API outcome.
- **SC-004**: An MCP-compatible client can discover the available tools and their required inputs without consulting repository source code or implementation internals.

## Assumptions

- The existing REST API remains the authoritative workflow surface and will be invoked by the MCP layer rather than replaced.
- The MCP server may run in the same repository and process boundary as the existing application for PoC scope.
- LangGraph remains an example consumer, but the tool interface is intentionally designed to be framework-agnostic.
- Existing business rules, idempotency behavior, and error semantics remain unchanged unless explicitly extended by this feature.
