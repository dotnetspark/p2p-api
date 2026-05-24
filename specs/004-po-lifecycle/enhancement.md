# Enhancement Notes: Purchase Order Lifecycle

## Purpose

This document explains why this feature intentionally deviates from the original
assignment only where the repo's phased feature structure changes how the
purchase-order portion is specified.

## Deviations From The Assignment

### 1. The broader P2P assignment was split so purchase-order lifecycle stands alone

The original assignment described a larger end-to-end Purchase-to-Pay flow. This
repository isolates the purchase-order lifecycle into its own feature rather than
specifying invoice matching and GL behavior in the same document.

**Why**:

- The project constitution requires phased execution with hard gates between feature
  slices.
- The purchase-order lifecycle provides a coherent business unit that can be planned,
  tested, and validated independently before invoice and GL features are added.

### 2. The query behavior is strengthened for agent decision-making

This feature expects the order-state query to return enough structured order and
receipt progress information for an agent to make a proceed-or-wait decision without
extra interpretation.

**Why**:

- The original assignment emphasizes that the API is machine-first.
- The repository constitution prioritizes autonomous machine interpretation and
  explicit workflow observability.

### 3. The CLOSED state is acknowledged but not completed in the PO feature itself

The original assignment includes `CLOSED` in the purchase-order lifecycle. This
feature references that future state for consistency but does not claim to implement
the later invoice/payment behavior that would move an order there.

**Why**:

- Closure depends on downstream invoice and payment features that are outside this
  feature's scope.
- Keeping the later state visible preserves coherence with the original assignment
  without expanding this feature beyond the intended slice.
