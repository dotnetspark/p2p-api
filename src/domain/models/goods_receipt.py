from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class GoodsReceiptLineInput:
    po_line_item_id: str
    qty_received: int


@dataclass(frozen=True)
class GoodsReceiptLineRecord:
    po_line_item_id: str
    qty_received: int


@dataclass(frozen=True)
class GoodsReceiptRecord:
    id: str
    po_id: str
    received_by: str
    received_at: datetime
    idempotency_key: str
    line_items: list[GoodsReceiptLineRecord]