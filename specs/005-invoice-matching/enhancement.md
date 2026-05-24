# Enhancement Notes: Invoice Matching

## Purpose

This document explains how the current repository version of invoice matching keeps
faith with the original assignment while fitting the repo's phased feature layout and
preserving prior draft decisions.

## Alignment With The Original Assignment

### 1. The original invoice-matching slice is preserved, even though the repo numbers it as `005`

The earlier draft referred to `feat/003-invoice-matching`. In this repository the
same business slice is implemented as `005-invoice-matching` because vendor
management and purchase-order lifecycle were split into separate earlier features and
completed first.

**Why**:

- The constitution requires phased execution and verification of earlier slices before
  later ones proceed.
- The underlying business capability remains the same: invoice creation plus 3-way
  matching against purchase-order receipt progress.

### 2. The draft clarifications are now encoded into the feature design

The earlier draft left two points pending: re-matching after additional receipts and
the behavior when invoice amount exactly equals received value. The current feature
artifacts resolve those directly so planning and implementation do not depend on
unwritten assumptions.

**Resolved behavior**:

- Re-matching is allowed later after additional goods receipts arrive, but a new
  idempotency key is required for a fresh evaluation.
- Exact equality is not overbilling. It is still a warning if any lines remain open,
  and it is clean only when the purchase order is fully received.

### 3. The machine-first API is strengthened without changing the assignment's business intent

The original assignment asked for a fully machine-actionable 3-way match result. The
current spec makes that explicit by requiring next-action guidance, signed value
difference, full-receipt indicator, and line-level open exposure details in the match
responses.

**Why**:

- The constitution prioritizes autonomous agent interpretation.
- The earlier draft already pointed in this direction by requiring exact shortfall,
  proceed-or-wait guidance, and specific open-line reporting.