# Research: MCP Server Tools

## Decision: Use the official Python MCP SDK and expose one mounted streamable HTTP server under `/mcp`

**Rationale**: The feature is specifically about exposing the existing P2P API as
MCP tools. The official Python SDK already supports tool registration, schema
generation, streamable HTTP transport, and ASGI mounting. Mounting one MCP server
into the current FastAPI app keeps deployment simple and avoids inventing a
parallel runtime.

**Alternatives considered**:

- Build a custom JSON-RPC adapter by hand: rejected because it recreates protocol
  behavior the SDK already provides.
- Use stdio as the primary transport: rejected because the repo is already a web
  service and streamable HTTP fits hosted and multi-client consumption better.

## Decision: Keep the MCP layer in-process and call the existing schemas and domain services directly

**Rationale**: The current FastAPI routes are already thin wrappers around schema
validation, domain services, and shared error mapping. Reusing those same request
and response schemas inside the MCP adapter preserves behavior without adding a new
application layer or paying loopback HTTP cost.

**Alternatives considered**:

- Call the local REST endpoints through `httpx` loopback requests: rejected because
  it adds avoidable transport overhead, couples the adapter to a server URL, and
  makes tests noisier without improving correctness.
- Extract a new intermediate orchestration layer before implementing MCP: rejected
  because the current routes are already thin and a new abstraction would exceed the
  minimum scope required by the feature.

## Decision: Expose one stable snake_case tool per current public workflow operation

**Rationale**: The machine-first API surface is already organized around stable
workflow actions. Mirroring that surface with predictable snake_case tool names
keeps discovery straightforward and avoids creating framework-specific wrappers.
This slice therefore exposes the current public operations, including vendor
eligibility, purchase-order lifecycle, invoice lifecycle, vendor exposure, and
credit-check lookup.

**Alternatives considered**:

- Expose a single generic `call_api` tool: rejected because it weakens discovery,
  shifts contract knowledge back onto the caller, and defeats the point of MCP tool
  introspection.
- Group operations into a few broad workflow tools: rejected because it would blur
  idempotency boundaries and hide existing business transitions.

## Decision: Require `idempotency_key` on every mutating tool and make `correlation_id` optional but always surfaced

**Rationale**: The existing HTTP API requires explicit idempotency headers on
mutating operations. Keeping that requirement in MCP preserves deterministic replay
instead of silently generating keys that agents cannot safely reuse. Correlation IDs
can still default the same way the HTTP middleware does, but every tool result must
return the concrete ID used.

**Alternatives considered**:

- Auto-generate idempotency keys inside the MCP adapter: rejected because retries
  would no longer be caller-controlled or reproducible.
- Require correlation IDs on every tool call: rejected because the existing HTTP API
  already supports generation when omitted and the same ergonomics are acceptable
  here as long as the result echoes the chosen identifier.

## Decision: Return a shared structured envelope for both success and failure tool outcomes

**Rationale**: The MCP layer must not collapse rich REST outcomes into plain text.
Each tool will therefore return a structured envelope containing `ok`,
`status_code`, `correlation_id`, and either `data` or `error`. Failed tool calls
will also be marked as MCP errors so generic clients can distinguish success from
failure without parsing messages.

**Alternatives considered**:

- Return only free-form strings from tools: rejected because it violates the repo's
  machine-readability goals.
- Return raw domain models without envelope metadata: rejected because the caller
  would lose transport-equivalent details such as status class and correlation ID.

## Decision: Preserve REST response payloads rather than inventing MCP-specific business DTOs

**Rationale**: The repository already has Pydantic models that define the current
agent-facing payloads. Reusing those response shapes inside `data` keeps REST as the
authoritative contract and minimizes semantic drift between the two interfaces.

**Alternatives considered**:

- Redesign payloads for tool-first ergonomics: rejected because it would create two
  authoritative contracts for the same workflow.
- Return raw ORM/domain objects: rejected because they are not the published
  machine-facing contract.

## Decision: Test the feature through real MCP client sessions against the mounted app

**Rationale**: The critical risk in this feature is not only tool registration but
transport behavior, discovery, result structure, and replay semantics over MCP. The
test strategy must therefore connect through a real client session and invoke tools
end-to-end, while still keeping focused unit coverage for adapter helpers.

**Alternatives considered**:

- Test only the tool functions directly: rejected because it would miss protocol and
  transport integration issues.
- Rely solely on manual inspection with MCP Inspector: rejected because the repo
  requires repeatable automated verification.

## Decision: Keep the MCP surface framework-agnostic and document LangGraph only as a consumer example

**Rationale**: The user explicitly wants MCP as the general integration model. The
server therefore describes business tools, not LangGraph nodes or agent-graph
concepts, while remaining fully consumable by LangGraph or any other MCP-compatible
client.

**Alternatives considered**:

- Model tools around LangGraph-specific terminology: rejected because it narrows the
  feature to one consumer and adds needless coupling.
- Omit consumer guidance entirely: rejected because the quickstart should still show
  how a generic MCP client discovers and uses the server.
