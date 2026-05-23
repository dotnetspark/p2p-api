from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from src.api.dependencies.error_handlers import error_to_response
from src.api.schemas.vendor_eligibility import VendorEligibilityResponse
from src.domain.services.vendor_eligibility_service import VendorEligibilityService
from src.persistence.database import get_db_session

router = APIRouter()


@router.get("/vendors/{vendor_id}/eligibility", response_model=VendorEligibilityResponse)
def get_vendor_eligibility(
    vendor_id: str,
    request: Request,
    session: Session = Depends(get_db_session),
) -> VendorEligibilityResponse | JSONResponse:
    result = VendorEligibilityService().get_eligibility(session, vendor_id)
    if result.error is not None:
        return error_to_response(request, result.error)
    return VendorEligibilityResponse(**result.value.__dict__)
