# Data Model: Purchase Order Lifecycle

## Overview

This feature models the purchase-order lifecycle from draft creation through
submission, receipt accumulation, and order-state visibility. Invoice creation,
matching, approval, and payment remain outside this feature, although the order model
acknowledges a later `CLOSED` state for continuity with the broader assignment and a
future one-invoice-per-purchase-order constraint.

## Entities

### PurchaseOrder

**Purpose**: Represents a procurement commitment against a vendor and anchors the
order lifecycle state.

**Fields**:

- `id`: Stable purchase-order identifier
- `vendor_id`: Foreign key to `Vendor.id`
- `status`: One of `DRAFT`, `SUBMITTED`, `RECEIVED`, or `CLOSED`
- `created_at`: Timestamp when the order was first created
- `submitted_at`: Optional timestamp populated when the order is submitted
- `invoice_id`: Optional future foreign key to `Invoice.id`, modeled as zero-or-one
  relationship and left unset by this feature

**Validation rules**:

- `vendor_id` must reference an existing active vendor at creation time
- `status = DRAFT` on initial creation
- Receipt recording is allowed only when `status = SUBMITTED`
- `status = RECEIVED` once all line items have reached full ordered quantity
- `status = CLOSED` is reserved for the later GL Posting feature when invoice payment
  is recorded
- `invoice_id`, when later populated, must remain unique per purchase order

### POLineItem

**Purpose**: Represents an ordered SKU or material on a purchase order and tracks
receipt progress.

**Fields**:

- `id`: Stable line identifier
- `po_id`: Foreign key to `PurchaseOrder.id`
- `sku`: Ordered item identifier
- `description`: Human-readable line description
- `qty_ordered`: Quantity requested on the order
- `qty_received`: Cumulative quantity received across all accepted receipts
- `unit_cost`: Agreed unit price

**Validation rules**:

- Each purchase order must contain at least one line item
- `qty_ordered` must be greater than zero
- `unit_cost` must be greater than zero
- `0 <= qty_received <= qty_ordered`
- `qty_received` may only increase through accepted goods receipts
- Receipt handling must add newly accepted quantities to the existing cumulative
  `qty_received` value rather than replace it

### GoodsReceipt

**Purpose**: Represents a receipt event against a submitted purchase order.

**Fields**:

- `id`: Stable goods-receipt identifier
- `po_id`: Foreign key to `PurchaseOrder.id`
- `received_by`: Actor or system identity that recorded the receipt
- `received_at`: Timestamp when the receipt was recorded
- `idempotency_key`: Caller-supplied key used to make retries safe

**Validation rules**:

- `po_id` must reference an order in `SUBMITTED` state at receipt time
- Duplicate `idempotency_key` for the same logical receipt must not create duplicate
  receipt effects

### GoodsReceiptLineItem

**Purpose**: Represents one line-level quantity received within a receipt event.

**Fields**:

- `id`: Stable receipt-line identifier
- `goods_receipt_id`: Foreign key to `GoodsReceipt.id`
- `po_line_item_id`: Foreign key to `POLineItem.id`
- `qty_received`: Quantity received for that line in this event

**Validation rules**:

- `qty_received` must be greater than zero
- The sum of all goods-receipt line quantities for a PO line item may never exceed
  `POLineItem.qty_ordered`

### PurchaseOrderProgressView

**Purpose**: Derived machine-readable view returned to callers when they query a
purchase order.

**Fields**:

- `po_id`
- `vendor_id`
- `status`
- `line_items`: Ordered, received, remaining quantities and full-receipt indicator per line
- `receipts`: Historical receipt events included for audit and traceability

## Relationships

- `Vendor 1 -> many PurchaseOrder`
- `PurchaseOrder 1 -> many POLineItem`
- `PurchaseOrder 1 -> many GoodsReceipt`
- `GoodsReceipt 1 -> many GoodsReceiptLineItem`
- `POLineItem 1 -> many GoodsReceiptLineItem`
- `PurchaseOrder 1 -> zero or one Invoice` (future feature boundary only)

## Business Invariants

- Inactive vendors cannot receive new purchase orders
- Goods cannot be received against an order that has never been submitted
- Cumulative received quantity on a line may never exceed the ordered quantity
- Accepted receipts must accumulate against the existing line total instead of
  replacing prior `qty_received` values
- Rejecting a receipt attempt must not alter previously accepted receipt totals
- A purchase order may be linked to at most one invoice in the broader lifecycle
- A purchase order becomes `RECEIVED` once every line item reaches its full ordered
  quantity
- A single purchase-order query must expose enough line-level progress for an agent to
  determine whether invoicing should proceed or wait

## State Transitions

### PurchaseOrder

- `DRAFT -> SUBMITTED`: valid when the agent submits a draft purchase order
- `SUBMITTED -> RECEIVED`: valid automatically when all line items are fully received
- `RECEIVED -> CLOSED`: reserved for the later GL Posting feature when invoice
  payment is recorded

Invalid transitions must return machine-readable business errors that identify the
current state and required state for the attempted action.
