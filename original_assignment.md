# Builder Interview Challenge — Dev Track

**Role:** Builder 2 (Engineering Acceleration & ERP Modernization)  
**Format:** 60-minute live vibe-coding session with the interviewer  
**Tools:** Use whatever you want — Cursor, Copilot, ChatGPT, Claude. That's the point.

---

## The Scenario

You've just joined a modernization strike team inheriting a 20-year-old ERP system for a mid-size building materials distributor. The existing system is a black box of stored procedures and undocumented business logic. Your first mission: stand up a clean, modern **Purchase-to-Pay (P2P) API** that an AI agent can use to navigate the procurement lifecycle autonomously.

This API will become the **tool-calling interface** for an agentic workflow — so design it like a machine is the primary consumer, not a human.

---

## The Domain Model

You're working with these core entities. Keep the schema simple but relational and financially coherent.

| Entity          | Key Fields                                                                           |
| --------------- | ------------------------------------------------------------------------------------ |
| `Vendor`        | id, name, payment_terms (NET30/NET60), is_active                                     |
| `PurchaseOrder` | id, vendor_id, status (DRAFT/SUBMITTED/RECEIVED/CLOSED), line_items, created_at      |
| `POLineItem`    | id, po_id, sku, description, qty_ordered, qty_received, unit_cost                    |
| `GoodsReceipt`  | id, po_id, received_by, received_at, line_items                                      |
| `Invoice`       | id, vendor_id, po_id, invoice_number, amount, status (PENDING/MATCHED/APPROVED/PAID) |
| `GLEntry`       | id, invoice_id, account_code, debit, credit, posted_at                               |

---

## Your Mission (60 min core, 30 min stretch)

### Core (must ship)

Build a working REST API that supports the following workflows. Use whatever stack you're comfortable with — Python/FastAPI is fine, TypeScript/Express is fine.

**1. PO Lifecycle**

- `POST /purchase-orders` — Create a draft PO against a vendor with line items
- `POST /purchase-orders/{id}/submit` — Submit for fulfillment
- `POST /purchase-orders/{id}/receive` — Record a goods receipt (supports partial receipt)
- `GET /purchase-orders/{id}` — Full PO detail including receipt status per line item

**2. Invoice Matching**

- `POST /invoices` — Create an invoice linked to a PO
- `POST /invoices/{id}/match` — 3-way match: verify invoice amount against PO and goods receipt
  - Must reject if invoice amount > received goods value
  - Must flag if partial receipt is pending

**3. GL Posting**

- `POST /invoices/{id}/approve` — Approve a matched invoice and auto-generate GL entries
  - Debit: `AP Control` account
  - Credit: `Expense` account based on vendor category
  - Reject if invoice is not in MATCHED status

**4. Basic validation throughout**

- Inactive vendors cannot have new POs
- Cannot receive more qty than ordered
- Cannot approve an unmatched invoice

### Stretch Goals (if time allows)

- `GET /vendors/{id}/exposure` — Return total outstanding AP liability for a vendor
- A lightweight agent wrapper: given a natural language instruction like `"Create a PO for 50 units of SKU-9234 from vendor ACME at $12.50/unit"`, parse and execute via your own API
- An async background task that flags invoices where the vendor's total open AP exceeds their credit limit

---

## What We're Watching For

We're not grading on lines of code. We're watching **how you work**.

- **Clarifying questions** — Do you ask about edge cases before building? (What happens on a partial match? What if the vendor has multiple open POs?)
- **AI leverage** — Are you prompting effectively, or are you typing boilerplate by hand? Do you iterate when the output is wrong?
- **Context management** — Do you break the problem into chunks and feed the AI the right context at each step?
- **Agent-first thinking** — Are your endpoints clean, predictable, and machine-friendly? Good error codes, consistent shapes, typed contracts.
- **Financial logic** — Does your 3-way match actually protect against overpayment? Does the GL posting balance?
- **Shipping** — Working code we can run locally by the end. Not perfect — working.

---

## Setup Notes

- Use SQLite or an in-memory DB (SQLAlchemy + SQLite is fine) — no infra setup required
- Seed 2-3 vendors, 5-10 SKUs on startup so we can call endpoints immediately
- A `README.md` with one-line run instructions is enough
- Tests are a bonus, not a requirement for core scope

---

## Conversation Starters (we'll use these to probe during the session)

Be ready to discuss:

- How would you expose this API as a **tool** for a LangGraph agent?
- If an agent calls `/invoices/{id}/match` and gets a partial match failure, what should it do next? How do you encode that in the response?
- Where would you add observability so you can trace what an agent did across a full P2P workflow?
