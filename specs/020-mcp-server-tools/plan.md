# Implementation Plan: MCP Server Tools

**Branch**: `feat/039-mcp-server-tools` | **Date**: 2026-05-27 | **Spec**: `specs/020-mcp-server-tools/spec.md`

**Input**: Feature specification from `/specs/020-mcp-server-tools/spec.md`

## Summary

Expose the current agent-facing purchase-to-pay workflow as MCP tools using the
official Python MCP SDK, mounted as a streamable HTTP endpoint inside the
existing FastAPI application. The MCP layer will remain a thin adapter that
reuses the current request/response schemas and domain services, returning
structured tool results that preserve idempotency, correlation IDs, follow-up
handles such as `credit_check_id`, and the existing machine-readable business
error semantics.

## Technical Context

**Primary Dependencies**: [e.g., FastAPI, UIKit, LLVM or NEEDS CLARIFICATION]

**Storage**: [if applicable, e.g., PostgreSQL, CoreData, files or N/A]

**Testing**: [e.g., pytest, XCTest, cargo test or NEEDS CLARIFICATION]

**Target Platform**: [e.g., Linux server, iOS 15+, WASM or NEEDS CLARIFICATION]

**Project Type**: [e.g., library/cli/web-service/mobile-app/compiler/desktop-app or NEEDS CLARIFICATION]

**Performance Goals**: [domain-specific, e.g., 1000 req/s, 10k lines/sec, 60 fps or NEEDS CLARIFICATION]

**Constraints**: [domain-specific, e.g., <200ms p95, <100MB memory, offline-capable or NEEDS CLARIFICATION]

**Scale/Scope**: [domain-specific, e.g., 10k users, 1M LOC, 50 screens or NEEDS CLARIFICATION]

## Constitution Check

_GATE: Must pass before Phase 0 research. Re-check after Phase 1 design._

- Contract clarity: Every planned endpoint, event, and error shape is explicitly defined
  for machine interpretation, including stable codes and recovery semantics.
- Workflow determinism: Resource states, allowed transitions, idempotency strategy, and
  stale-write handling are documented for every mutating operation.
- Verification-first delivery: Contract artifacts, examples, and failing contract tests
  are identified before implementation tasks are approved.
- Traceability: Correlation IDs, audit-relevant entity identifiers, and structured
  telemetry requirements are captured for new flows.
- PoC guardrails: Any simplification, stubbed dependency, or deferred production concern
  is listed explicitly and shown not to weaken external contract semantics.

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
src/
├── api/
│   ├── dependencies/
│   ├── routes/
│   └── schemas/
├── core/
├── domain/
├── mcp/
│   ├── server.py
│   ├── models.py
│   └── tools.py
├── persistence/
└── main.py

tests/
├── contract/
│   └── test_mcp_tools.py
├── integration/
│   └── test_mcp_tools.py
└── unit/
    └── test_mcp_server.py
```

**Structure Decision**: Keep the existing layered FastAPI service and add a small
`src/mcp/` adapter package instead of introducing a second application or a
network loopback client. The adapter will reuse the current API schemas and
domain services, while `src/main.py` mounts the MCP server under a dedicated
streamable HTTP path and manages the MCP session lifecycle alongside the current
app lifespan.

## Complexity Tracking

No constitution violations or justified complexity exceptions were identified in planning.
