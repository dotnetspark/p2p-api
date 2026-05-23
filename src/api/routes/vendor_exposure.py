from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.api.schemas.vendor_exposure import VendorExposureResponse
from src.domain.services.vendor_exposure_service import VendorExposureService
from src.persistence.database import get_db_session

router = APIRouter()


@router.get("/vendors/{vendor_id}/exposure", response_model=VendorExposureResponse)
def get_vendor_exposure(
    vendor_id: str,
    session: Session = Depends(get_db_session),
) -> VendorExposureResponse:
    result = VendorExposureService().get_exposure(session, vendor_id)
    return VendorExposureResponse(**result.__dict__)
