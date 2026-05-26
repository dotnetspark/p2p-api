# Interview Edge Cases

Use this document as a quick review sheet for concrete repository issues that are better treated as fix candidates than open-ended interview tradeoffs.

## Seed Data Integrity

### Seeded invoices must not point at missing purchase orders

- Existing seed invoices reference `PO-1001`, `PO-1002`, `PO-1003`, and `PO-2001`
- If those purchase orders are not seeded, demo data becomes internally inconsistent
- That conflicts with the assignment expectation that seeded data should let the interviewer call endpoints immediately
- The strongest fix is to make the seed set coherent so seeded invoices always reference seeded purchase orders

## Accounting Invariants

### Balanced-posting validation should check balance, not just a two-line assumption

- `gl_entries_are_balanced` should answer whether debits equal credits
- A separate rule can enforce exactly two entries when that workflow requires it
- An empty list should still be treated as invalid

### GL integrity failures should not look retryable

- Missing or unbalanced persisted GL entries are integrity failures, not transient service outages
- Agents should not see those as `503` with `retryable=true`
- The safer behavior is a non-retryable server error classification

## API Contract Hygiene

### Remove dead fallbacks when the contract is already explicit

- `InvoiceApprovalResult` already carries `credit_check_id`
- The response mapper should access it directly instead of using a defensive `getattr` fallback that no longer serves a purpose

## Review Heuristic

When deciding whether something belongs in this document, ask:

- Does it violate an explicit assignment expectation or a hard correctness invariant?
- Would leaving it in place produce misleading runtime behavior rather than just an interview discussion point?

If yes, it belongs here.