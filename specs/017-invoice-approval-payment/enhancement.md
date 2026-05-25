# Enhancement Notes: Invoice Approval and Payment

## Purpose

This document answers two questions for this feature: what the original assignment
actually requested, and where this repository intentionally deviates from or sharpens
that request and why.

## Alignment With The Original Assignment

### 1. Invoice approval and GL posting remain the core assignment behavior

The original assignment explicitly requires `POST /invoices/{id}/approve` to approve
a matched invoice, generate GL entries, and reject approval when the invoice is not
in `MATCHED` status. This feature keeps that business slice intact.

**Why**:

- Approval and GL posting are part of the assignment's core scope, not a repo-only
  addition.
- Preserving that behavior keeps this feature anchored to the interview prompt rather
  than inventing a different downstream finance workflow.

## Deviations From The Assignment

### 2. Payment and automatic PO closure are added beyond the original assignment

The original assignment stops at invoice approval and GL posting. This repository adds
`POST /invoices/{id}/pay` and closes the linked purchase order when payment succeeds
so the post-match lifecycle can complete inside the repo's phased feature sequence.

**Why**:

- The repo is organized as progressive P2P slices, and stopping at approval would
  leave the financial lifecycle intentionally incomplete.
- The earlier purchase-order feature already acknowledged `CLOSED` as a future state,
  so payment-driven closure is the natural follow-on capability.

### 3. Expense-account selection is made deterministic with a hardcoded mapping and fallback

The original assignment says the expense side of the GL posting should be based on
vendor category, but it does not define how that category is resolved or what should
happen when the category is missing. This repository makes that behavior explicit by
using a hardcoded category-to-account map with an unclassified fallback.

**Why**:

- The machine-first API needs approval outcomes that are deterministic and do not
  require a human to repair missing classification before the workflow can continue.
- The feature plan explicitly requires that approval must never fail solely because
  vendor category context is missing or unmapped.

**Implemented repo rule**:

- Because the current vendor master data does not carry an explicit category field,
  this repository derives a category heuristically from the vendor name when it can,
  then applies the hardcoded account map.
- If no rule matches the current vendor data, approval falls back to
  `UNCLASSIFIED_EXPENSE` rather than failing.

### 4. Payment completion is modeled as business completion, not treasury integration

The original assignment does not define a payment operation at all. This repository
therefore models payment as an internal business completion step rather than a bank or
AP disbursement integration.

**Why**:

- The interview scope is to deliver a coherent local workflow, not a production-grade
  treasury or settlement integration.
- This keeps the enhancement focused on lifecycle completion while preserving a clean
  path for future external payment integration if needed.

### 5. The one-invoice-per-PO PoC constraint remains in force for payment-driven closure

The original assignment requires invoices to be linked to purchase orders, but it does
not require a strict one-to-one invoice-to-PO relationship. This repository continues
the earlier PoC assumption that one invoice is linked to one purchase order, which is
why payment of that invoice is sufficient to close the order in this slice.

**Why**:

- The repo already scoped invoice matching around a single-invoice-per-PO model for
  simplicity and deterministic workflow behavior.
- Automatic closure on payment would need more cumulative invoice-balance logic if the
  repository were already modeling multiple invoices per purchase order.
