# Interview Conversation Starters

Use these prompts to prepare for discussion about the repository during an interview, code review, or portfolio walkthrough.

## How To Use This Document

- Treat each item as a discussion prompt, not a script.
- Start with the business reason, then explain the design choice, then the tradeoff.
- When relevant, distinguish between prompt fidelity and production-grade design.

## Core Discussion Prompts

### 1. Why is the API machine-first?

Talk through why the repository optimizes for autonomous callers:

- stable endpoint shapes
- deterministic recovery guidance
- idempotent mutating operations
- structured business errors
- explicit next actions in workflow responses

### 2. Why use Specification-Driven Development for an interview-sized project?

Useful angle:

- the assignment is short, but the business rules are easy to get subtly wrong
- SDD kept user intent, data shape, contracts, and implementation traceable
- the feature-slice approach prevented mixing lifecycle stages before earlier rules were stable

### 3. Why break the assignment into features instead of shipping one large implementation?

Useful angle:

- vendor validation, PO lifecycle, matching, approval, payment, and credit monitoring are separate controls
- each slice became independently testable
- the repo history shows how the system became more complete without losing behavioral clarity

### How does the API help an agent recover from failure?

Useful angle:

- invoice matching returns exact shortfall and next-step context
- approval rejects invalid states without partial side effects
- idempotency prevents duplicate obligations or duplicate GL posting on retries
- credit checks use a durable `credit_check_id` instead of leaving background work opaque

### Why is vendor exposure a natural checkpoint?

Useful angle:

- exposure is where finance decisions become risk-aware
- surfacing alert state there keeps the API smaller than adding a dedicated alert surface
- it matches the vendor-wide nature of open AP and credit-limit evaluation

## Tradeoff Prompts

### 6. Why use FastAPI `BackgroundTasks` instead of a queue or worker?

Useful angle:

- it is a bounded PoC decision
- it preserves non-blocking behavior without adding infrastructure overhead
- the durable `credit_check_id` keeps the public contract compatible with a future queue-backed implementation

### 6a. Why require a submitted purchase order before invoice registration?

Useful angle:

- the repo now requires the PO to be at least `SUBMITTED` before invoice registration
- the original assignment said invoices are linked to a PO, but left draft-PO invoicing ambiguous
- requiring submission makes the payable workflow easier to defend because draft usually means the obligation is not yet committed
- the interesting discussion is now why that ambiguity was resolved this way and whether production systems should go further with line-level commitment controls

### Why should error codes describe business meaning instead of pseudo-states?

Useful angle:

- `NO_INVOICE` is not a real purchase-order state, even if it can be used internally as a shorthand rule
- agent-facing error codes and messages are easier to trust when they name the real business condition directly
- that makes error-symbol design part of the machine-first contract, not just string polish

### Why can in-process background work leave `PENDING` checks behind after a restart?

Useful angle:

- `BackgroundTasks` is acceptable for a PoC, but it does not give durable execution guarantees across process death
- that creates a good discussion point about PoC pragmatism versus production durability
- a queue, outbox, or startup recovery pass would be the next hardening step

### Why keep one active credit alert per vendor instead of flagging each invoice?

Useful angle:

- the risk condition is vendor-wide, not invoice-local
- one active alert avoids duplicate active records for the same breach
- the repo still preserves traceability back to the triggering invoice and check

### Should invoices have a dedicated read endpoint like purchase orders do?

Useful angle:

- purchase orders already have a `GET` endpoint, so the missing invoice read path is easy to notice
- adding it would make the resource model more symmetric for agent workflows
- leaving it out is still defensible because the original assignment never required it

### Why derive the expense account from vendor name heuristics?

Useful angle:

- the assignment required vendor-category-based expense posting without defining a full master-data model
- the repo chose deterministic local rules plus `UNCLASSIFIED_EXPENSE`
- this kept approval from failing purely because category data was incomplete

### 9. GL posting direction: prompt fidelity vs accounting correctness

This started as a strong conversation starter because the original assignment explicitly says:

- Debit `AP Control`
- Credit `Expense`

Standard accrual accounting would normally reverse that direction when recognizing an approved invoice:

- Debit expense
- Credit accounts payable

Useful angle:

- the repo now corrects the prompt instead of following it literally
- that choice is grounded in the constitution's requirement for financial correctness
- the important design point is not just spotting the discrepancy, but documenting the intentional deviation clearly in specs and ADRs

### 10. When should you follow the prompt literally, and when should you deviate?

Useful angle:

- follow the prompt when the requirement is explicit and the exercise is testing execution discipline
- deviate only when the prompt is ambiguous, incomplete, or produces behavior you can defend correcting
- when deviating, document it clearly in specs, ADRs, tests, and reviewer-facing notes

### Where would you add observability first in a PoC like this?

Useful angle:

- correlation IDs already exist, which gives a starting point for request tracing
- a middleware or service-boundary log strategy would improve operational visibility quickly
- this is a good way to explain how you would evolve the system without pretending it already has full production telemetry

## Architecture Prompts

### 11. Why keep HTTP, domain logic, and persistence separate?

Useful angle:

- the service layer owns business rules
- the API layer translates request and response concerns
- the persistence layer owns storage details
- that separation makes behavior easier to test and reason about when the workflow grows

### 12. Why prefer real SQLite in tests instead of mocks?

Useful angle:

- the assignment is about business correctness, not isolated framework trivia
- real persistence catches lifecycle and replay issues that mocks often hide
- the repo uses contract and integration tests to validate real behavior, not invented behavior

## Interview Close-Out Prompts

### 13. If you had more time, what would you change next?

Strong answers include:

- replace in-process background tasks with a queue-backed worker
- formalize vendor classification instead of name heuristics
- extend accounting coverage beyond the current two-line approval journal when the domain requires accrual variations
- add richer observability and trace correlation across the full workflow

### 14. What is the strongest design decision in the repo?

Strong answers include:

- durable async credit-check querying
- explicit idempotency and replay handling
- feature-slice decomposition with spec traceability
- machine-readable match outcomes that guide the next agent action
