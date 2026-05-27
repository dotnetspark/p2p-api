# Data Model: MCP Server Tools

## Overview

This feature does not add persistence entities or change the existing purchase,
invoice, vendor, or credit-check schemas. Instead, it introduces a small logical
adapter model for turning MCP tool invocations into the same machine-readable
workflow results already defined by the REST API.

## Entities

### MCPToolCatalogEntry

**Purpose**: Represents one published MCP tool and its mapping to an existing
workflow operation.

**Fields**:

- `name`: Stable MCP tool name, such as `create_purchase_order`
- `category`: Logical grouping such as `vendor`, `purchase_order`, or `invoice`
- `mutating`: Boolean flag indicating whether the tool requires an idempotency key
- `underlying_method`: Existing REST verb for traceability only
- `underlying_path`: Existing REST path for traceability only
- `summary`: Short machine-usable description of the business action

**Validation rules**:

- Each published tool maps to exactly one current public workflow operation
- `name` remains stable once published
- `mutating = true` implies the tool input requires `idempotency_key`

### MCPInvocationContext

**Purpose**: Carries the adapter-level metadata needed to preserve deterministic
recovery and traceability for a single tool call.

**Fields**:

- `correlation_id`: Optional caller-supplied identifier; generated if omitted
- `idempotency_key`: Required for mutating tools, omitted for read-only tools

**Validation rules**:

- Mutating tools must reject calls that omit `idempotency_key`
- Read-only tools must not require `idempotency_key`
- Every result envelope must include the concrete `correlation_id` used

### MCPToolSuccessEnvelope

**Purpose**: Represents a successful tool call while preserving the original
workflow payload and transport-equivalent context.

**Fields**:

- `ok`: Always `true`
- `tool_name`: The MCP tool that was invoked
- `status_code`: HTTP-equivalent success status from the underlying workflow
- `correlation_id`: Concrete trace identifier used for the call
- `data`: Existing REST response payload for the workflow operation

**Validation rules**:

- `data` reuses the published REST response shape for that operation
- `status_code` matches the underlying route behavior, such as `201` for create or
  `200` for standard success
- Success payloads preserve follow-up fields such as `next_action` and
  `credit_check_id`

### MCPToolFailureEnvelope

**Purpose**: Represents a business or infrastructure failure without losing the
existing machine-readable error semantics.

**Fields**:

- `ok`: Always `false`
- `tool_name`: The MCP tool that was invoked
- `status_code`: HTTP-equivalent failure status from the shared error mapping
- `correlation_id`: Concrete trace identifier used for the call
- `error`:
  - `code`
  - `category`
  - `retryable`
  - `message`
  - `correlation_id`

**Validation rules**:

- `error.code`, `error.category`, and `error.retryable` mirror the existing
  `ServiceError` contract exactly
- Tool failures are marked as MCP errors in addition to returning this structured
  envelope
- Validation failures caused by missing required MCP arguments are rejected before
  business execution begins

### Tool Payload Reuse

**Purpose**: Reuse the existing REST request and response schemas rather than
inventing a second business contract.

**Reused request payloads**:

- Vendor lookup arguments
- Purchase-order creation and goods-receipt payloads
- Invoice creation payload

**Reused response payloads**:

- `VendorEligibilityResponse`
- `VendorExposureResponse`
- `PurchaseOrderResponse`
- `InvoiceResponse`
- `InvoiceMatchResponse`
- `InvoiceApprovalResponse`
- `InvoicePaymentResponse`
- `CreditCheckStatusResponse`

**Validation rules**:

- The MCP `data` payload must stay semantically aligned with the corresponding REST
  response model
- If a REST response schema changes in a later feature, the MCP contract for that
  operation must be regenerated from the updated source shape

## Relationships

- `MCPToolCatalogEntry 1 -> 1 underlying workflow operation`
- `MCPInvocationContext 1 -> 1 MCP tool call`
- `MCPToolSuccessEnvelope 1 -> 1 reused REST success payload`
- `MCPToolFailureEnvelope 1 -> 1 reused ServiceError payload`

## State Transitions

### Mutating tool invocation

- `REQUESTED -> SUCCEEDED`: the underlying workflow commits successfully and the MCP
  tool returns a success envelope
- `REQUESTED -> REPLAYED`: the underlying workflow recognizes a matching
  idempotency key and the MCP tool returns the original logical success envelope
- `REQUESTED -> FAILED`: the underlying workflow returns a business or
  infrastructure error and the MCP tool returns a failure envelope marked as an MCP
  error

### Read-only tool invocation

- `REQUESTED -> SUCCEEDED`: the underlying query returns data successfully
- `REQUESTED -> FAILED`: the underlying query returns a business or infrastructure
  error and the MCP tool returns a failure envelope marked as an MCP error

## Derived Rules

- No persistence migration is introduced by this feature
- The MCP catalog exposes 11 tools covering the current public workflow surface
- Mutating tools require explicit idempotency keys; read tools do not
- Correlation IDs may be caller-supplied or adapter-generated, but are always echoed
  back in the result envelope
- Follow-up identifiers such as `purchase_order_id`, `invoice_id`, and
  `credit_check_id` remain in the business payload instead of being hidden in MCP
  metadata
