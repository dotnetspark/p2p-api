# Project Constitution — p2p-api

## Purpose

This constitution establishes the governing philosophy for the p2p-api project.
It is the supreme authority over all architectural and quality decisions made
during specification, planning, and implementation.

It defines how this project thinks about building software — not what it builds
or how specific features are implemented. Implementation details belong in
`data-model.md` and `contracts/`. Domain rules belong in `spec.md`.
This document contains neither.

## Article I — Machine-Readability as a First Principle

This system is built for AI agents as its primary consumers. Every design decision
— from how success is communicated to how failures are structured — must optimise
for autonomous machine interpretation and recovery without human intermediation.

When a human consumer and an agent consumer require different design choices,
the agent's needs take precedence.

## Article II — Financial Correctness Over Convenience

This system handles procurement and accounting obligations. Correctness of financial
logic is non-negotiable and cannot be bypassed for convenience, speed, or agent
autonomy. Any operation that could result in an organisation paying for goods not
received, or accounting entries that do not balance, must be prevented by the
system itself — not delegated to the caller's discipline.

## Article III — Test-First Imperative

No implementation code is written before the behaviour it implements is defined
as a testable acceptance criterion in `spec.md`. When tests are generated they
are written before implementation code, validated to fail, then used to drive
implementation.

Test files are not generated automatically. They are produced only on explicit
human request. When produced, the order is: contract tests → integration tests
→ unit tests. Tests use real infrastructure — no mocking of the persistence layer.

## Article IV — Layered Architecture

Every implementation enforces a strict separation between the HTTP boundary,
business logic, and persistence. No layer may reach into a layer above it.
Business rules live in one place only — never scattered across the system.

This separation exists so that specifications can describe behaviour without
knowing how it is delivered, and implementations can be regenerated from
specifications without carrying forward structural debt.

## Article V — Schema Change Governance

No entity, field, relationship, or status enumeration may be added, renamed,
or removed without:

1. A corresponding update to the affected `spec.md` in user story terms
2. A regenerated `data-model.md` via `/speckit.plan`
3. An ADR in `docs/adr/` documenting rationale and migration impact
4. Human approval before any implementation reflects the change

The authoritative source for current schema is always `data-model.md` inside
the relevant feature spec directory.

## Article VI — Phased Execution with Hard Gates

The project advances in phases defined by the sequence of feature specs. No work
on a later phase begins until all specs in the current phase are verified working
by a human and tagged. Phase membership is established at specification time —
earlier specs form earlier phases.

The phase gate exists because partial systems with unverified behaviour are harder
to reason about than no system at all. A working earlier phase is more valuable
than a nearly-working one with later phase scaffolding mixed in.

## Article VII — Simplicity and Anti-Abstraction

Start with the minimum number of moving parts that satisfy the specification.
Add complexity only when the specification demands it and an ADR justifies it.
Future-proofing is prohibited — build for the specified scope.

Use chosen frameworks and libraries directly. Do not wrap them in custom
abstractions unless the specification produces a documented, unavoidable need.
Every abstraction layer must justify its existence against the user stories it serves.

## Article VIII — Observability as Architecture

The system must be inspectable at every step of a workflow — not as an
afterthought, but as a first-class architectural concern. Every action an
agent takes must be traceable from entry to outcome without requiring access
to internal state.

Trace correlation — linking a chain of agent actions across multiple operations
— is a design requirement, not a monitoring add-on. Its specific implementation
is defined in `contracts/` and `plan.md`.

## Article IX — Integration-First Testing

Tests must validate behaviour in realistic environments. Prefer real persistence
over mocks. Prefer actual service instances over stubs. Contract tests are defined
before implementation — they are the agreement between specification and code.

## Article X — Traceability of Intent

Every change to code must be traceable to a change in a specification. A commit
that modifies implementation without a corresponding specification change is a gap
between intent and implementation — the exact gap SDD exists to eliminate.

The mechanics of how traceability is enforced — branch naming, commit conventions,
PR rules, changelog discipline — are operational instructions defined elsewhere.
This article establishes only that traceability is non-negotiable.

## Amendment Process

Amendments to this constitution require:

1. A GitHub Issue documenting the proposed change and rationale
2. An ADR in `docs/adr/` with impact assessment
3. Human approval before any implementation reflects the amendment
4. Version bump to this file's header

Minor clarifications (typos, formatting) do not require an ADR but must be
committed with `docs(constitution): <description>`.

**Version**: 1.0.0 | **Ratified**: 2026-05-22 | **Last Amended**: 2026-05-22
