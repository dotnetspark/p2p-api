from __future__ import annotations

from fastapi import APIRouter, Depends, Header, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from src.api.dependencies.error_handlers import error_to_response
from src.api.schemas.purchase_order import (
    CreateGoodsReceiptRequest,
    CreatePurchaseOrderRequest,
    PurchaseOrderResponse,
)
from src.domain.models.goods_receipt import GoodsReceiptLineInput
from src.domain.models.purchase_order import PurchaseOrderLineInput
from src.domain.services.goods_receipt_service import GoodsReceiptService
from src.domain.services.purchase_order_service import PurchaseOrderService
from src.persistence.database import get_db_session


router = APIRouter()


@router.post("/purchase-orders", response_model=PurchaseOrderResponse, status_code=201)
def create_purchase_order(
    payload: CreatePurchaseOrderRequest,
    request: Request,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    session: Session = Depends(get_db_session),
) -> PurchaseOrderResponse | JSONResponse:
    result = PurchaseOrderService().create_purchase_order(
        session=session,
        vendor_id=payload.vendor_id,
        line_items=[
            PurchaseOrderLineInput(
                sku=line_item.sku,
                description=line_item.description,
                qty_ordered=line_item.qty_ordered,
                unit_cost=line_item.unit_cost,
            )
            for line_item in payload.line_items
        ],
        idempotency_key=idempotency_key,
    )
    if result.error is not None:
        return error_to_response(request, result.error)
    return PurchaseOrderResponse.from_domain(result.value)


@router.post("/purchase-orders/{purchase_order_id}/submit", response_model=PurchaseOrderResponse)
def submit_purchase_order(
    purchase_order_id: str,
    request: Request,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    session: Session = Depends(get_db_session),
) -> PurchaseOrderResponse | JSONResponse:
    result = PurchaseOrderService().submit_purchase_order(session, purchase_order_id, idempotency_key)
    if result.error is not None:
        return error_to_response(request, result.error)
    return PurchaseOrderResponse.from_domain(result.value)


@router.post("/purchase-orders/{purchase_order_id}/receive", response_model=PurchaseOrderResponse)
def receive_purchase_order(
    purchase_order_id: str,
    payload: CreateGoodsReceiptRequest,
    request: Request,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    session: Session = Depends(get_db_session),
) -> PurchaseOrderResponse | JSONResponse:
    result = GoodsReceiptService().receive_goods(
        session=session,
        purchase_order_id=purchase_order_id,
        received_by=payload.received_by,
        line_items=[
            GoodsReceiptLineInput(
                po_line_item_id=line_item.po_line_item_id,
                qty_received=line_item.qty_received,
            )
            for line_item in payload.line_items
        ],
        idempotency_key=idempotency_key,
    )
    if result.error is not None:
        return error_to_response(request, result.error)
    return PurchaseOrderResponse.from_domain(result.value)


@router.get("/purchase-orders/{purchase_order_id}", response_model=PurchaseOrderResponse)
def get_purchase_order(
    purchase_order_id: str,
    request: Request,
    session: Session = Depends(get_db_session),
) -> PurchaseOrderResponse | JSONResponse:
    result = PurchaseOrderService().get_purchase_order(session, purchase_order_id)
    if result.error is not None:
        return error_to_response(request, result.error)
    return PurchaseOrderResponse.from_domain(result.value)