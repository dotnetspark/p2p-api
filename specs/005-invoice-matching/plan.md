# Implementation Plan: Invoice Matching

**Branch**: `005-invoice-matching` | **Date**: 2026-05-24 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/005-invoice-matching/spec.md`

## Summary

Implement the invoice-registration and invoice-matching slice of the P2P API using
the existing Python 3.14, FastAPI, SQLAlchemy 2.x, and SQLite service without
changing version choices. The feature adds invoice registration against a specific
vendor and purchase order, enforces duplicate detection on the composite
`(vendor_id, invoice_number)`, and evaluates invoice support against goods actually
received rather than ordered value. Match outcomes are explicitly split into three
contract states: hard reject with exact shortfall and next action (`422`), matched
with open-exposure warning (`202`), and clean match (`200`). New invoices begin in a
pending state, registration responses tell the agent to request matching next, and
every match response includes overall value difference plus line-level open exposure
details. Matching remains idempotent per request, while previously matched invoices
may be re-matched after additional receipts arrive by issuing a new match request
with a fresh idempotency key.

## Technical Context

**Language/Version**: Python 3.14

**Primary Dependencies**: FastAPI, SQLAlchemy 2.x, Pydantic v2, Uvicorn

**Storage**: SQLite

**Testing**: pytest, FastAPI TestClient or httpx, real SQLite-backed integration tests

**Target Platform**: Single-process REST API service for local development and PoC deployment

**Project Type**: Web service

**Performance Goals**: Invoice register and match operations complete within 250 ms p95 on PoC-scale seeded data

**Constraints**: Duplicate invoice detection is keyed by `(vendor_id, invoice_number)`; invoice registration must reject incoherent vendor and purchase-order combinations; new invoices must begin in `PENDING`; match evaluation must use receipt-backed value `sum(qty_received * unit_cost)`; match responses must distinguish hard reject (`422`), partial receipt warning (`202`), and clean match (`200`); every match response must include invoice amount, received value, signed difference, all-lines-fully-received indicator, and open-line details; a retried identical request with the same idempotency key must replay the original logical outcome; re-evaluating an invoice after new receipts requires a new idempotency key; correlation IDs and machine-readable error codes are mandatory; persistence-layer mocking is prohibited

**Scale/Scope**: PoC scope for a mid-size distributor with tens to low hundreds of purchase orders and invoices, one invoice per purchase order in the broader lifecycle, and multiple rematch attempts as receipts accumulate

## Constitution Check

_GATE: Must pass before Phase 0 research. Re-check after Phase 1 design._

### Pre-Design Gate Review

- Contract clarity: PASS. The plan fixes distinct status codes, success and warning payloads, stable business error codes, and retry guidance for agent consumption.
- Workflow determinism: PASS. Registration, duplicate detection, rematch semantics, and receipt-backed decision rules are explicit before implementation.
- Verification-first delivery: PASS. This plan generates contract, quickstart, research, and data-model artifacts before implementation tasks.
- Traceability: PASS. Correlation IDs, invoice identifiers, purchase-order identifiers, match outcome snapshots, and next-action signals are captured in the design.
- PoC guardrails: PASS. The feature stays within the existing FastAPI and SQLite service and does not add architecture beyond what the user stories require.

### Post-Design Gate Review

- Contract clarity: PASS. [contracts/invoice-matching.openapi.yaml](./contracts/invoice-matching.openapi.yaml) defines stable request and response shapes for invoice registration and the three match outcomes.
- Workflow determinism: PASS. [data-model.md](./data-model.md) defines invoice state progression, composite duplicate rules, receipt-backed support calculation, and rematch behavior under idempotency.
- Verification-first delivery: PASS. [quickstart.md](./quickstart.md) provides executable validation flows for registration, duplicate rejection, hard reject match, partial warning match, clean match, and rematch after new receipts.
- Traceability: PASS. Contracts require correlation IDs and preserve identifiers needed to trace invoice creation, match evaluation, and downstream approval decisions.
- PoC guardrails: PASS. [research.md](./research.md) documents why the feature reuses the current stack and keeps matching synchronous while preserving the caller-visible contract.

## Project Structure

### Documentation (this feature)

```text
specs/005-invoice-matching/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── invoice-matching.openapi.yaml
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

**Structure Decision**: Extend the existing single FastAPI service and reuse the established layered API, core, domain, and persistence structure. Add invoice-specific route, schema, model, service, and repository components while reusing the shared idempotency mechanism and purchase-order receipt data rather than introducing a second service or a parallel accounting abstraction.

## Complexity Tracking

No constitution violations or complexity exceptions require justification for this
feature.
