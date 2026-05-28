## User

I need to register invoice {invoice_number} for purchase order {purchase_order_id}
from vendor {vendor_id}, for the amount of {invoice_amount}.

## Assistant

Before I raise the invoice, I'll check the current state of purchase order
{purchase_order_id}. The invoice can only be created once the order has been
submitted; if goods have already been received I'll include that context so you
have the full picture.

## Assistant

Once the preconditions are satisfied, I'll confirm the full details — vendor
{vendor_id}, order {purchase_order_id}, invoice {invoice_number}, amount
{invoice_amount}, and an idempotency key — and ask for your approval before
registering the invoice. After that I'll keep the invoice ID and credit check ID
in context so we can progress through matching, approval, and payment.

## Assistant

If you'd like to see what a typical invoice payload looks like, I can pull up an
example from {uri_example_create_invoice}.
