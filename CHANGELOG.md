# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog.

## [Unreleased]

### Added

- Purchase-order lifecycle endpoints for draft creation, submission, additive goods receipt tracking, and order-state queries [#4]

### Fixed

- Purchase-order create, submit, and receive now reject conflicting idempotency-key reuse with stable business errors instead of silent replay or false infrastructure failure [#4]
- Removed API-layer dependency leaks from domain and persistence by introducing typed service errors and API-only HTTP mapping [#2]

## [0.1.0] - 2026-05-23

### Added

- Vendor eligibility and AP exposure endpoints for agent-facing vendor management [#001]
