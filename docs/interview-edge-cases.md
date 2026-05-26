# Interview Edge Cases

Use this document to prepare for boundary-condition and ambiguity questions that may come up during an interview discussion.

The goal here is not to list repo bugs. The goal is to capture business or contract edge cases that are either already addressed in the repo or still open to discussion.

Items that are primarily design tradeoffs or interview prompts belong in `docs/interview-conversation-starters.md` instead of this document.

## Already Addressed

### Partial receipt but invoice amount is still covered

- If the invoice amount is less than or equal to received value, matching can still succeed even when the purchase order is not fully received
- The repo treats this as a warning outcome rather than a hard failure
- This is already addressed in the invoice-matching feature design

### Invoice amount exactly equals received value

- Exact equality is not overbilling
- The repo treats it as clean only when the purchase order is fully received
- If lines remain open, it is still a warning case rather than a blocked one

### Re-matching after more goods are received

- A previously blocked or warning match can be re-evaluated after additional receipts arrive
- The repo already addresses this, but requires a new idempotency key for a fresh evaluation

### Missing vendor category for expense posting

- The assignment requires expense posting based on vendor category but does not define a complete vendor-category model
- The repo already addresses this by falling back to `UNCLASSIFIED_EXPENSE`

### Retrying create or approve after a credit check was already scheduled

- Without a replay rule, retries could create duplicate checks or duplicate alert side effects
- The repo already addresses this by replaying the same `credit_check_id`

## Still Open To Discussion

### Should one purchase order allow multiple invoices?

- The assignment does not require a one-to-one invoice-to-PO relationship
- The repo narrows scope to one invoice per purchase order for PoC simplicity
- In production, multiple invoices per purchase order is the more plausible model

### Should payment be modeled as lifecycle completion or treasury integration?

- The assignment stops at approval and GL posting
- The repo adds payment as a local business completion step
- An interviewer may ask whether that is sufficient or whether settlement integration should exist

## Interview Use

For each edge case, be ready to answer three things:

- what the assignment explicitly says
- what the repo currently does
- what you would keep or change in a production-grade version
