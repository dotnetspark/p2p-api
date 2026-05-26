# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog.

## [Unreleased]

### Fixed

- Seed data now backs seeded invoices with matching purchase orders, GL integrity failures are non-retryable 500s, and approval response mapping removes a dead credit-check fallback [#31]
- README assignment and SDD Mermaid flowcharts now use simplified GitHub-compatible labels after the remaining render failures on the repo homepage [#27]
- README SDD Mermaid flow now renders more reliably on GitHub by simplifying node labels in the remaining failing diagram [#25]
- README Mermaid credit-alert flow now renders correctly on GitHub by removing parser-breaking endpoint placeholders from flowchart node labels [#23]

### Added

- Added focused interview-prep notes covering conversation starters and concrete edge-case review topics [#29]
- Repository README now documents the project scope, SDD workflow, feature map, architecture, and interview framing with Mermaid diagrams [#21]
- Invoice create and approve now return replay-safe `credit_check_id` values, persist vendor credit checks, expose `GET /credit-checks/{id}`, and surface active credit alerts on vendor exposure [#19]

## [0.4.0] - 2026-05-24

### Added

- POST /invoices/{id}/approve now approves matched invoices and creates exactly two balanced GL entries with replay-safe responses [#17]
- POST /invoices/{id}/pay now marks approved invoices paid and closes linked receipted purchase orders [#17]

### Fixed

- Approval now derives expense accounts deterministically from repo-local vendor classification rules and falls back to UNCLASSIFIED_EXPENSE instead of blocking on missing category data [#17]

## [0.3.0] - 2026-05-24

### Added

- Invoice registration and 3-way match endpoints with pending-state creation, exact shortfall handling, partial-receipt warnings, clean match outcomes, and replay-safe rematching [#003]

### Fixed

- Invoice match responses now return signed value difference, open-line exposure details, and deterministic next actions for autonomous recovery [#003]

## [0.2.0] - 2026-05-24

### Added

- Purchase-order lifecycle endpoints for draft creation, submission, additive goods receipt tracking, and order-state queries [#4]

### Fixed

- Purchase-order create, submit, and receive now reject conflicting idempotency-key reuse with stable business errors instead of silent replay or false infrastructure failure [#4]
- Removed API-layer dependency leaks from domain and persistence by introducing typed service errors and API-only HTTP mapping [#2]

## [0.1.0] - 2026-05-23

### Added

- Vendor eligibility and AP exposure endpoints for agent-facing vendor management [#001]
