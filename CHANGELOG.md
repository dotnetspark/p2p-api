# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog.

## [Unreleased]

### Added

- Purchase-order lifecycle endpoints for draft creation, submission, additive goods receipt tracking, and order-state queries [#4]
- Invoice registration and 3-way match endpoints with pending-state creation, exact shortfall handling, partial-receipt warnings, clean match outcomes, and replay-safe rematching [#003]

### Fixed

- Purchase-order create, submit, and receive now reject conflicting idempotency-key reuse with stable business errors instead of silent replay or false infrastructure failure [#4]
- Removed API-layer dependency leaks from domain and persistence by introducing typed service errors and API-only HTTP mapping [#2]
- Invoice match responses now return signed value difference, open-line exposure details, and deterministic next actions for autonomous recovery [#003]

## [0.1.0] - 2026-05-23

### Added

- Vendor eligibility and AP exposure endpoints for agent-facing vendor management [#001]
