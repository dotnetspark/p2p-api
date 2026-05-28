## User

I'd like to place an order for {qty_ordered} units of {sku} — '{description}'
at {unit_cost} each — with vendor {vendor_id}.

## Assistant

Before I create anything, let me check that vendor {vendor_id} is currently active
and eligible to receive new obligations. I may also review their outstanding
exposure if you'd like that context first.

## Assistant

Once eligibility is confirmed, I'll summarise the order — vendor {vendor_id},
{qty_ordered} × {sku} ({description}) at {unit_cost} each — and ask for your
confirmation before raising the draft. I'll include a unique idempotency key so
the request is safe to retry. After creation I'll keep the purchase order ID and
line item ID ready for the submit and receive steps.

## Assistant

If you'd like to see a concrete example of a purchase order payload before we
proceed, I can pull one up from {uri_example_create_po}.
