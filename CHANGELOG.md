# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog.

## [Unreleased]

### Added

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
