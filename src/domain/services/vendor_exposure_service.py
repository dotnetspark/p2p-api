from __future__ import annotations

from sqlalchemy.orm import Session

from src.core.errors import ServiceError, vendor_not_found
from src.core.results import Result
from src.domain.models.vendor import OutstandingPaymentObligationSummary
from src.persistence.repositories.credit_alert_repository import CreditAlertRepository
from src.persistence.repositories.invoice_repository import InvoiceRepository
from src.persistence.repositories.vendor_repository import VendorRepository


class VendorExposureService:
    def __init__(
        self,
        vendor_repository: VendorRepository | None = None,
        invoice_repository: InvoiceRepository | None = None,
        credit_alert_repository: CreditAlertRepository | None = None,
    ) -> None:
        self.vendor_repository = vendor_repository or VendorRepository()
        self.invoice_repository = invoice_repository or InvoiceRepository()
        self.credit_alert_repository = credit_alert_repository or CreditAlertRepository()

    def get_exposure(self, session: Session, vendor_id: str) -> Result[OutstandingPaymentObligationSummary, ServiceError]:
        vendor = self.vendor_repository.get_by_id(session, vendor_id)
        if vendor is None:
            return Result.fail(vendor_not_found(vendor_id))
        aggregate = self.invoice_repository.get_exposure_aggregate(session, vendor_id)
        summary = OutstandingPaymentObligationSummary.zero(
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
        active_credit_alert = self.credit_alert_repository.get_active_by_vendor_id(session, vendor_id)
        if active_credit_alert is not None:
            summary = OutstandingPaymentObligationSummary(
                vendor_id=summary.vendor_id,
                vendor_name=summary.vendor_name,
                as_of_timestamp=summary.as_of_timestamp,
                outstanding_total_amount=summary.outstanding_total_amount,
                open_invoice_count=summary.open_invoice_count,
                included_invoice_statuses=summary.included_invoice_statuses,
                active_credit_alert=active_credit_alert,
            )
        return Result.ok(summary)
