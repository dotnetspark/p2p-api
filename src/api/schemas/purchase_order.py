from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from src.api.schemas.common import APIModel
from src.domain.models.purchase_order import PurchaseOrder


class PurchaseOrderLineInputRequest(APIModel):
    sku: str
    description: str
    qty_ordered: int
    unit_cost: Decimal


class CreatePurchaseOrderRequest(APIModel):
    vendor_id: str
    line_items: list[PurchaseOrderLineInputRequest]


class GoodsReceiptLineInputRequest(APIModel):
    po_line_item_id: str
    qty_received: int


class CreateGoodsReceiptRequest(APIModel):
    received_by: str
    line_items: list[GoodsReceiptLineInputRequest]


class PurchaseOrderLineProgressResponse(APIModel):
    po_line_item_id: str
    sku: str
    description: str
    qty_ordered: int
    qty_received: int
    qty_remaining: int


class GoodsReceiptLineResponse(APIModel):
    po_line_item_id: str
    qty_received: int


class GoodsReceiptResponse(APIModel):
    goods_receipt_id: str
    received_by: str
    received_at: datetime
    line_items: list[GoodsReceiptLineResponse]


class PurchaseOrderResponse(APIModel):
    purchase_order_id: str
    vendor_id: str
    status: str
    line_items: list[PurchaseOrderLineProgressResponse]
    receipts: list[GoodsReceiptResponse]

    @classmethod
    def from_domain(cls, purchase_order: PurchaseOrder) -> "PurchaseOrderResponse":
        return cls(
            purchase_order_id=purchase_order.id,
            vendor_id=purchase_order.vendor_id,
            status=purchase_order.status,
            line_items=[
                PurchaseOrderLineProgressResponse(
                    po_line_item_id=line_item.id,
                    sku=line_item.sku,
                    description=line_item.description,
                    qty_ordered=line_item.qty_ordered,
                    qty_received=line_item.qty_received,
                    qty_remaining=line_item.qty_remaining,
                )
                for line_item in purchase_order.line_items
            ],
            receipts=[
                GoodsReceiptResponse(
                    goods_receipt_id=receipt.id,
                    received_by=receipt.received_by,
                    received_at=receipt.received_at,
                    line_items=[
                        GoodsReceiptLineResponse(
                            po_line_item_id=line_item.po_line_item_id,
                            qty_received=line_item.qty_received,
                        )
                        for line_item in receipt.line_items
                    ],
                )
                for receipt in purchase_order.receipts
            ],
        )