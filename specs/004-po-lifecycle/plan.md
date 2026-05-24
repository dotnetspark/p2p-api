# Implementation Plan: Purchase Order Lifecycle

**Branch**: `feat/004-po-lifecycle` | **Date**: 2026-05-23 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/004-po-lifecycle/spec.md`

## Summary

Implement the purchase-order lifecycle slice of the P2P API using the existing
Python 3.14, FastAPI, SQLAlchemy 2.x, and SQLite service without changing version
choices. The feature adds draft purchase-order creation, explicit submission for
fulfilment, append-only goods receipt recording across multiple deliveries, and a
full order-state query with per-line receipt progress so an agent can decide whether
invoicing should proceed. Receipt updates must accumulate prior accepted quantities
rather than replace them, and the design must preserve the later business rule that
each purchase order may relate to at most one invoice. The `CLOSED` status remains
part of the state model for continuity, but its transition is deferred to the later
GL Posting feature when invoice payment is recorded.

## Technical Context

**Language/Version**: Python 3.14

**Primary Dependencies**: FastAPI, SQLAlchemy 2.x, Pydantic v2, Uvicorn

**Storage**: SQLite

**Testing**: pytest, FastAPI TestClient or httpx, real SQLite-backed integration tests

**Target Platform**: Single-process REST API service for local development and PoC deployment

**Project Type**: Web service

**Performance Goals**: Purchase-order create, submit, receive, and query operations complete within 250 ms p95 on PoC-scale seeded data

**Constraints**: Only active vendors may receive new purchase orders; goods receipt is invalid before submission; receipt processing must add new accepted quantities to existing `qty_received` totals instead of replacing them; cumulative received quantity may never exceed ordered quantity; each purchase order may be associated to at most one invoice in the broader lifecycle; the `CLOSED` state must be modeled but not transitioned by this feature; mutating operations must be safe for agent retries; correlation IDs and machine-readable error codes are mandatory; persistence-layer mocking is prohibited

**Scale/Scope**: PoC scope for a mid-size distributor with a seeded vendor catalog, tens to low hundreds of purchase orders, and multiple receipt events per order

## Constitution Check

_GATE: Must pass before Phase 0 research. Re-check after Phase 1 design._

### Pre-Design Gate Review

- Contract clarity: PASS. Phase 1 defines the four purchase-order lifecycle capabilities and stable business error catalog for machine-first consumption.
- Workflow determinism: PASS. The spec constrains draft submission, receipt eligibility, additive receipt accumulation, over-receipt rejection, and full-receipt completion behavior while leaving `CLOSED` for a later feature.
- Verification-first delivery: PASS. This plan produces contracts, examples, quickstart flows, and a data model before tasks are generated.
- Traceability: PASS. Correlation IDs, order identifiers, receipt identifiers, and per-line progress are captured in the contract and quickstart artifacts.
- PoC guardrails: PASS. SQLite, local seeding, and single-service deployment remain explicit PoC simplifications that do not weaken external workflow semantics.

### Post-Design Gate Review

- Contract clarity: PASS. [contracts/purchase-order-lifecycle.openapi.yaml](./contracts/purchase-order-lifecycle.openapi.yaml) defines stable success and error shapes for create, submit, receive, and query.
- Workflow determinism: PASS. [data-model.md](./data-model.md) defines order states, additive receipt accumulation rules, the one-invoice-per-order boundary, and full-receipt completion semantics while keeping `CLOSED` unimplemented here.
- Verification-first delivery: PASS. [quickstart.md](./quickstart.md) provides executable validation flows for draft creation, submission, receipt recording, and order-state queries.
- Traceability: PASS. Contracts require correlation IDs and capture identifiers needed to follow order creation, submission, and receipt events.
- PoC guardrails: PASS. [research.md](./research.md) documents the chosen simplifications without changing caller-visible behavior.

## Project Structure

### Documentation (this feature)

```text
specs/004-po-lifecycle/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── purchase-order-lifecycle.openapi.yaml
└── tasks.md
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
│   ├── models/
│   ├── rules/
│   └── services/
├── persistence/
│   ├── models/
│   ├── repositories/
│   └── seed/
└── main.py

tests/
├── contract/
├── integration/
└── unit/
```

**Structure Decision**: Extend the existing single FastAPI service and reuse the established layered API/core/domain/persistence structure so purchase-order lifecycle behavior stays isolated from HTTP concerns, preserves additive receipt semantics, and remains compatible with the later one-invoice-per-order lifecycle constraint.

## Complexity Tracking

No constitution violations or complexity exceptions require justification for this
feature.
