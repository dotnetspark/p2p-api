# Implementation Plan: Invoice Approval and Payment

**Branch**: `feat/017-invoice-approval-payment` | **Date**: 2026-05-24 | **Spec**: `specs/017-invoice-approval-payment/spec.md`

**Input**: Feature specification from `/specs/017-invoice-approval-payment/spec.md`

## Summary

Implement the post-match invoice lifecycle in the existing P2P API by adding two
deterministic operations: invoice approval and invoice payment. Approval is allowed
only from `MATCHED`, generates exactly two synchronous and balanced GL entries, and
classifies the expense side through a hardcoded vendor-category account map with an
`UNCLASSIFIED_EXPENSE` fallback. Payment is allowed only from `APPROVED`, marks the
invoice `PAID`, and closes the linked purchase order using the existing PO lifecycle
rules.

## Technical Context

**Language/Version**: Python 3.14

**Primary Dependencies**: FastAPI, SQLAlchemy 2.x, Pydantic v2, Uvicorn

**Storage**: SQLite via SQLAlchemy ORM and existing repository patterns

**Testing**: pytest, FastAPI test client / httpx-based contract and integration tests

**Target Platform**: Local and CI-hosted API execution on Windows/Linux developer environments

**Project Type**: Backend web service

**Performance Goals**: Approval and payment remain synchronous single-resource mutations with deterministic replay and interview-scale latency expectations

**Constraints**: Exactly two GL rows per approval; GL rows must balance; approval must never fail because vendor category is missing or unmapped; payment must trigger PO `CLOSED`; no skipped lifecycle steps; external contract remains machine-readable and idempotent

**Scale/Scope**: Proof-of-concept workflow for low-volume transactional use, preserving the repository's current one-invoice-per-PO assumption

## Constitution Check

_GATE: Must pass before Phase 0 research. Re-check after Phase 1 design._

- Contract clarity: Satisfied. The feature defines explicit request/response shapes and stable error codes in `contracts/invoice-approval-payment.openapi.yaml`.
- Workflow determinism: Satisfied. The data model and research document the allowed invoice transitions `MATCHED -> APPROVED -> PAID`, idempotent replay expectations, and purchase-order closure behavior.
- Verification-first delivery: Satisfied. Contract, quickstart examples, research decisions, and entity rules are defined before implementation tasks.
- Traceability: Satisfied. The contract requires `X-Correlation-ID`, and approval/payment responses carry stable entity identifiers needed for audit and retry handling.
- PoC guardrails: Satisfied. Hardcoded account mapping, fallback classification, and business-only payment completion are explicit scope choices that do not weaken the external contract.

## Project Structure

### Documentation (this feature)

```text
specs/017-invoice-approval-payment/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── invoice-approval-payment.openapi.yaml
└── tasks.md
```

### Source Code (repository root)

```text
src/
├── api/
│   ├── routes/
│   └── schemas/
├── core/
├── domain/
│   ├── models/
│   ├── rules/
│   └── services/
└── persistence/
    ├── models/
    └── repositories/

tests/
├── contract/
├── integration/
└── unit/
```

**Structure Decision**: Continue within the existing single-service backend. Approval and payment touch API routes, request/response schemas, domain services, persistence models/repositories, and contract/integration tests. No new project boundary is justified because the accounting behavior is tightly coupled to invoice lifecycle transitions already implemented in this repository.

## Phase 0 Research Outcomes

- Reuse the existing FastAPI and SQLAlchemy stack rather than split accounting into a separate service.
- Make approval synchronous and deterministic so success always implies two persisted GL entries.
- Resolve vendor-category mapping through a hardcoded lookup plus `UNCLASSIFIED_EXPENSE` fallback.
- Model payment as a distinct business step after approval, not a side effect of approval.
- Reuse the existing idempotency framework for safe retries on approval and payment.

## Phase 1 Design Outcomes

- The core persisted additions are invoice approval/payment timestamps and a new `GLEntry` entity linked to invoices.
- The approval contract returns exactly two generated GL entry summaries so clients can validate balanced posting.
- The payment contract returns both invoice and purchase-order terminal statuses so agents can confirm lifecycle completion without extra reads.
- The feature remains aligned with the original assignment for approval and GL posting, while payment-triggered PO closure is documented as the requested extension for this slice.

## Complexity Tracking

No constitution violations or justified complexity exceptions were identified.
