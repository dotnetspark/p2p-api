# Implementation Plan: Vendor Management

**Branch**: `feat/001-vendor-management` | **Date**: 2026-05-23 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-vendor-management/spec.md`

## Summary

Implement an agent-first vendor management slice for the P2P API using Python 3.14,
FastAPI, SQLAlchemy 2.x, and SQLite. The feature exposes deterministic vendor
eligibility and AP exposure read capabilities, relies on pre-seeded vendor master
data, and returns server-computed exposure values so the calling agent never needs to
perform arithmetic to decide whether to proceed.

## Technical Context

**Language/Version**: Python 3.14

**Primary Dependencies**: FastAPI, SQLAlchemy 2.x, Pydantic v2, Uvicorn

**Storage**: SQLite

**Testing**: pytest, FastAPI TestClient or httpx, real SQLite-backed integration tests

**Target Platform**: Single-process REST API service for local development and PoC deployment

**Project Type**: Web service

**Performance Goals**: Vendor eligibility and exposure lookups complete within 200 ms p95 on PoC-scale seeded data

**Constraints**: Vendors are pre-seeded at startup with no create/update endpoints; exposure responses must pre-compute derived values; machine-readable errors and correlation IDs are mandatory; persistence-layer mocking is prohibited

**Scale/Scope**: PoC scope for a mid-size distributor with a single service, a seeded vendor catalog, and tens to low hundreds of active open invoices

## Constitution Check

_GATE: Must pass before Phase 0 research. Re-check after Phase 1 design._

### Pre-Design Gate Review

- Contract clarity: PASS. Phase 1 defines explicit contracts for vendor eligibility,
  vendor exposure, and the shared machine-readable error catalog.
- Workflow determinism: PASS. Read operations are deterministic, and the inactive
  vendor rule is centralized as a business invariant that downstream mutating flows
  must enforce using the same error semantics.
- Verification-first delivery: PASS. Contract artifacts, data model, and quickstart
  examples are created before implementation tasks.
- Traceability: PASS. Correlation ID handling and vendor/invoice identifiers are
  captured in the contract and quickstart artifacts.
- PoC guardrails: PASS. SQLite and startup seeding are explicit PoC simplifications
  that do not weaken caller-visible contract guarantees.

### Post-Design Gate Review

- Contract clarity: PASS. [contracts/vendor-management.openapi.yaml](./contracts/vendor-management.openapi.yaml) defines stable success and error shapes.
- Workflow determinism: PASS. [data-model.md](./data-model.md) defines the unpaid-invoice inclusion rule and the inactive-vendor invariant.
- Verification-first delivery: PASS. [quickstart.md](./quickstart.md) provides executable validation flows for the contract before implementation begins.
- Traceability: PASS. Contracts require correlation IDs and identify vendor and invoice references used in exposure calculations.
- PoC guardrails: PASS. Seeding and SQLite limitations are documented in [research.md](./research.md) and do not alter the external API behavior.

## Project Structure

### Documentation (this feature)

```text
specs/001-vendor-management/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── vendor-management.openapi.yaml
└── tasks.md
```

### Source Code (repository root)

```text
src/
├── api/
│   ├── dependencies/
│   ├── routes/
│   └── schemas/
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

**Structure Decision**: Use a single FastAPI service with explicit API, domain, and
persistence layers to satisfy the constitution's layered-architecture rule while
keeping the PoC deployment footprint minimal.

## Complexity Tracking

No constitution violations or complexity exceptions require justification for this
feature.
