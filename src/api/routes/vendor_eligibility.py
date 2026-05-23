from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.api.schemas.vendor_eligibility import VendorEligibilityResponse
from src.domain.services.vendor_eligibility_service import VendorEligibilityService
from src.persistence.database import get_db_session

router = APIRouter()


@router.get("/vendors/{vendor_id}/eligibility", response_model=VendorEligibilityResponse)
def get_vendor_eligibility(
    vendor_id: str,
    session: Session = Depends(get_db_session),
) -> VendorEligibilityResponse:
    result = VendorEligibilityService().get_eligibility(session, vendor_id)
    return VendorEligibilityResponse(**result.__dict__)
