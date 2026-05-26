from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from src.api.dependencies.error_handlers import error_to_response
from src.api.schemas.vendor_exposure import VendorExposureResponse
from src.domain.services.vendor_exposure_service import VendorExposureService
from src.persistence.database import get_db_session

router = APIRouter()


@router.get("/vendors/{vendor_id}/exposure", response_model=VendorExposureResponse)
def get_vendor_exposure(
    vendor_id: str,
    request: Request,
    session: Session = Depends(get_db_session),
) -> VendorExposureResponse | JSONResponse:
    result = VendorExposureService().get_exposure(session, vendor_id)
    if result.error is not None:
        return error_to_response(request, result.error)
    return VendorExposureResponse.from_domain(result.value)
