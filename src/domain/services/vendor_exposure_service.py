from __future__ import annotations

from sqlalchemy.orm import Session

from src.domain.models.vendor import OutstandingPaymentObligationSummary
from src.persistence.repositories.invoice_repository import InvoiceRepository
from src.persistence.repositories.vendor_repository import VendorRepository


class VendorExposureService:
    def __init__(
        self,
        vendor_repository: VendorRepository | None = None,
        invoice_repository: InvoiceRepository | None = None,
    ) -> None:
        self.vendor_repository = vendor_repository or VendorRepository()
        self.invoice_repository = invoice_repository or InvoiceRepository()

    def get_exposure(self, session: Session, vendor_id: str) -> OutstandingPaymentObligationSummary:
        vendor = self.vendor_repository.require_by_id(session, vendor_id)
        aggregate = self.invoice_repository.get_exposure_aggregate(session, vendor_id)
        return OutstandingPaymentObligationSummary.zero(
            vendor_id=vendor.id,
            vendor_name=vendor.name,
            included_invoice_statuses=aggregate.included_invoice_statuses,
        ) if aggregate.open_invoice_count == 0 else OutstandingPaymentObligationSummary(
            vendor_id=vendor.id,
            vendor_name=vendor.name,
            as_of_timestamp=aggregate.as_of_timestamp,
            outstanding_total_amount=aggregate.outstanding_total_amount,
            open_invoice_count=aggregate.open_invoice_count,
            included_invoice_statuses=aggregate.included_invoice_statuses,
        )
