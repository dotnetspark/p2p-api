# Implementation Plan: Vendor Credit Alert

**Branch**: `feat/019-vendor-credit-alert` | **Date**: 2026-05-25 | **Spec**: `specs/019-vendor-credit-alert/spec.md`

**Input**: Feature specification from `/specs/019-vendor-credit-alert/spec.md`

## Summary

Add a non-blocking vendor credit evaluation that runs after successful invoice creation
and invoice approval. Each triggering action pre-creates a `CreditCheckRecord` with a
UUID identifier in `PENDING` status, returns that identifier in a top-level
`credit_check_id` response field, and schedules a FastAPI
background task. The background task computes outstanding AP from invoices in
`PENDING`, `MATCHED`, and `APPROVED`, marks the check `COMPLETED`, and either upserts
the vendor's single active `CreditAlert` or clears a stale alert when the vendor is no
longer above the limit. Vendor exposure is extended to surface the current alert only
when a breach exists.

## Technical Context

**Language/Version**: Python 3.14

**Primary Dependencies**: FastAPI, Pydantic v2, SQLAlchemy 2.x

**Storage**: SQLite via SQLAlchemy ORM

**Testing**: pytest with contract, integration, and unit suites using real SQLite

**Target Platform**: Single-process FastAPI service running locally on Windows for PoC development

**Project Type**: Layered web service

**Performance Goals**: Successful invoice create and approve responses remain materially unchanged in latency because credit evaluation runs post-response; only UUID generation and one pending-record write are added to the request path.

**Constraints**: Preserve existing response data shapes except for adding a top-level `credit_check_id`; never block workflow actions on credit risk; idempotent replays must return the same `credit_check_id` and must not schedule duplicate background work; exceptions inside the background task must be logged silently and never surface to the caller; use the existing invoices router and vendor exposure endpoint rather than introducing a new router.

**Scale/Scope**: One current active credit alert per vendor, one credit-check record per successful logical create/approve action, no historical alert archive, no external queue or worker tier in this feature slice.

## Constitution Check

_GATE: Must pass before Phase 0 research. Re-check after Phase 1 design._

**Pre-Design Gate Review**

- Contract clarity: PASS. The plan defines changes to invoice create, invoice approve, `GET /credit-checks/{id}`, and vendor exposure, including deterministic credit-check identifiers and existing error semantics.
- Workflow determinism: PASS. `CreditCheckRecord` state transitions (`PENDING -> COMPLETED`), breach evaluation rules, replay-safe scheduling, and single-active-alert replacement rules are explicit.
- Verification-first delivery: PASS. Contract, data model, and quickstart artifacts are produced before any implementation work.
- Traceability: PASS. Correlation IDs remain part of the external contract, while `credit_check_id`, `alert_id`, `vendor_id`, and `triggering_invoice_id` provide internal and external traceability.
- PoC guardrails: PASS. FastAPI `BackgroundTasks` is an intentional PoC simplification that does not weaken the external contract because the caller already gets a durable query identifier.

## Project Structure

### Documentation (this feature)

```text
specs/019-vendor-credit-alert/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── vendor-credit-alert.openapi.yaml
└── tasks.md
```

### Source Code (repository root)

```text
src/
├── api/
│   ├── routes/
│   │   ├── invoices.py
│   │   └── vendor_exposure.py
│   └── schemas/
│       ├── invoice.py
│       └── vendor_exposure.py
├── domain/
│   ├── models/
│   └── services/
└── persistence/
    ├── models/
    └── repositories/

tests/
├── contract/
├── integration/
└── unit/
```

**Structure Decision**: Keep the existing layered FastAPI service. Add the public query path to the existing invoices router module, extend existing API schemas instead of introducing a parallel envelope abstraction, add new persistence/domain models for `CreditCheckRecord` and `CreditAlert`, and cover the feature through contract and integration tests first.

## Phase 0 Research Output

- Confirmed FastAPI `BackgroundTasks` is the smallest mechanism that satisfies the post-response requirement.
- Confirmed replay safety must be handled at scheduling time, not only inside the task.
- Confirmed vendor-level alerting remains the correct bounded model and is already documented by ADR.

## Phase 1 Design Output

- `data-model.md` defines `CreditCheckRecord`, `CreditAlert`, and the vendor exposure response extension.
- `contracts/vendor-credit-alert.openapi.yaml` defines create/approve credit-check identifier changes, the credit-check query endpoint, and the vendor exposure extension.
- `quickstart.md` defines the validation flow for create, approve, query, vendor exposure, and replay behavior.

## Post-Design Constitution Check

- Contract clarity: PASS. The contract now makes the caller-visible background workflow explicit without changing the business payloads.
- Workflow determinism: PASS. The plan captures pending/completed states, nullable breach fields while pending, alert replacement behavior, and replay-safe identifier reuse.
- Verification-first delivery: PASS. The generated artifacts are specific enough to support contract-first tests.
- Traceability: PASS. The new entities and contract shapes expose enough identifiers to link create/approve actions, checks, and alerts.
- PoC guardrails: PASS. The design keeps the single-process execution model explicit and bounded while preserving future migration room to a worker queue if ever needed.

## Complexity Tracking

No constitution violations or justified complexity exceptions were identified in planning.
