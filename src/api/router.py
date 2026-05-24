from fastapi import APIRouter

from src.api.routes.invoices import router as invoice_router
from src.api.routes.purchase_orders import router as purchase_order_router
from src.api.routes.vendor_eligibility import router as vendor_eligibility_router
from src.api.routes.vendor_exposure import router as vendor_exposure_router


def build_router() -> APIRouter:
    router = APIRouter()
    router.include_router(invoice_router, tags=["invoices"])
    router.include_router(purchase_order_router, tags=["purchase-orders"])
    router.include_router(vendor_eligibility_router, tags=["vendors"])
    router.include_router(vendor_exposure_router, tags=["vendors"])
    return router
