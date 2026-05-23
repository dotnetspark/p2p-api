# Enhancement Notes: Vendor Management

## Purpose

This document explains why this feature intentionally deviates from the original
assignment only insofar as that affects the purchase-order workflow and feature
sequencing in this repo.

## Deviations From The Assignment

### 1. Vendor eligibility was extracted ahead of the purchase-order feature

The original assignment treated inactive-vendor validation as a rule inside the
purchase-order workflow. This project moves that validation into a dedicated
prerequisite feature that the purchase-order lifecycle can depend on.

**Why**:

- The purchase-order workflow should not own the source of truth for whether a vendor
  is eligible to receive a new order.
- Pulling vendor eligibility into its own feature lets the later PO feature treat
  vendor validation as a clean prerequisite instead of embedding vendor-state logic in
  the middle of PO lifecycle behavior.
- This keeps the PO feature focused on order creation, submission, receipt progress,
  and order-state decisions.

### 2. Vendor exposure is grouped with vendor management instead of left entirely to later phases

The original assignment listed vendor exposure as a stretch capability rather than a
core purchase-order concern. This repo groups it with vendor management so the vendor
surface is coherent, even though it is not part of the PO lifecycle itself.

**Why**:

- This does not change the meaning of the PO workflow itself; it only changes where
  adjacent vendor-related behavior is specified.
- The repo is organized in phased slices, so vendor-facing capabilities are grouped
  together instead of being split between the PO feature and later financial features.
- Keeping vendor concerns together makes the dependency from the PO feature to vendor
  management explicit rather than implicit.
