from __future__ import annotations

import logging
from decimal import Decimal

from sqlalchemy.orm import Session

from src.core.errors import ServiceError, credit_check_not_found
from src.core.results import Result
from src.domain.models.vendor_credit import (
    CREDIT_CHECK_ACTION_APPROVE,
    CREDIT_CHECK_ACTION_CREATE,
    CREDIT_CHECK_STATUS_COMPLETED,
    CreditCheckQueryResult,
    CreditCheckRecord,
    complete_credit_check,
    create_credit_alert,
    create_pending_credit_check,
)
from src.persistence.database import session_scope
from src.persistence.repositories.credit_alert_repository import CreditAlertRepository
from src.persistence.repositories.credit_check_repository import CreditCheckRepository
from src.persistence.repositories.invoice_repository import InvoiceRepository
from src.persistence.repositories.vendor_repository import VendorRepository


logger = logging.getLogger(__name__)


class VendorCreditAlertService:
    def __init__(
        self,
        credit_check_repository: CreditCheckRepository | None = None,
        credit_alert_repository: CreditAlertRepository | None = None,
        invoice_repository: InvoiceRepository | None = None,
        vendor_repository: VendorRepository | None = None,
    ) -> None:
        self.credit_check_repository = credit_check_repository or CreditCheckRepository()
        self.credit_alert_repository = credit_alert_repository or CreditAlertRepository()
        self.invoice_repository = invoice_repository or InvoiceRepository()
        self.vendor_repository = vendor_repository or VendorRepository()

    def get_credit_check(
        self,
        session: Session,
        credit_check_id: str,
    ) -> Result[CreditCheckQueryResult, ServiceError]:
        credit_check = self.credit_check_repository.get_by_id(session, credit_check_id)
        if credit_check is None:
            return Result.fail(credit_check_not_found(credit_check_id))
        return Result.ok(
            CreditCheckQueryResult(
                status=credit_check.status,
                breached=credit_check.breached,
                alert_id=credit_check.alert_id,
            )
        )

    def create_pending_for_invoice_create(
        self,
        session: Session,
        vendor_id: str,
        invoice_id: str,
        correlation_id: str,
        idempotency_key: str,
    ) -> CreditCheckRecord:
        return self._create_pending_credit_check(
            session=session,
            vendor_id=vendor_id,
            invoice_id=invoice_id,
            triggering_action=CREDIT_CHECK_ACTION_CREATE,
            correlation_id=correlation_id,
            idempotency_key=idempotency_key,
        )

    def create_pending_for_invoice_approval(
        self,
        session: Session,
        vendor_id: str,
        invoice_id: str,
        correlation_id: str,
        idempotency_key: str,
    ) -> CreditCheckRecord:
        return self._create_pending_credit_check(
            session=session,
            vendor_id=vendor_id,
            invoice_id=invoice_id,
            triggering_action=CREDIT_CHECK_ACTION_APPROVE,
            correlation_id=correlation_id,
            idempotency_key=idempotency_key,
        )

    def dispatch_pending_credit_check(self, credit_check_id: str) -> None:
        try:
            with session_scope() as session:
                credit_check = self.credit_check_repository.get_by_id(session, credit_check_id)
                if credit_check is None:
                    raise ValueError(f"Credit check {credit_check_id} not found for dispatch.")
                if credit_check.status == CREDIT_CHECK_STATUS_COMPLETED:
                    return

                vendor = self.vendor_repository.get_by_id(session, credit_check.vendor_id)
                if vendor is None:
                    raise ValueError(f"Vendor {credit_check.vendor_id} not found for credit check {credit_check_id}.")

                triggering_invoice = self.invoice_repository.get_triggering_invoice(
                    session,
                    credit_check.triggering_invoice_id,
                )
                if triggering_invoice is None:
                    raise ValueError(
                        f"Invoice {credit_check.triggering_invoice_id} not found for credit check {credit_check_id}."
                    )

                outstanding_amount = self.calculate_exposure(session, credit_check.vendor_id)
                if outstanding_amount > vendor.credit_limit:
                    alert = create_credit_alert(
                        vendor_id=credit_check.vendor_id,
                        credit_check_id=credit_check.id,
                        triggering_invoice_id=triggering_invoice.invoice_id,
                        outstanding_amount=outstanding_amount,
                        credit_limit=vendor.credit_limit,
                    )
                    persisted_alert = self.credit_alert_repository.upsert_active(session, alert)
                    completed_credit_check = complete_credit_check(
                        credit_check,
                        breached=True,
                        alert_id=persisted_alert.id,
                    )
                else:
                    self.credit_alert_repository.clear_active(session, credit_check.vendor_id)
                    completed_credit_check = complete_credit_check(
                        credit_check,
                        breached=False,
                        alert_id=None,
                    )

                self.credit_check_repository.update(session, completed_credit_check)
        except Exception as error:
            self.log_background_failure(credit_check_id, error)

    def log_background_failure(self, credit_check_id: str, error: Exception) -> None:
        logger.exception("Credit check %s failed after response dispatch.", credit_check_id, exc_info=error)

    def calculate_exposure(self, session: Session, vendor_id: str) -> Decimal:
        aggregate = self.invoice_repository.get_exposure_aggregate(session, vendor_id)
        return aggregate.outstanding_total_amount

    def _create_pending_credit_check(
        self,
        session: Session,
        vendor_id: str,
        invoice_id: str,
        triggering_action: str,
        correlation_id: str,
        idempotency_key: str,
    ) -> CreditCheckRecord:
        credit_check = create_pending_credit_check(
            vendor_id=vendor_id,
            triggering_invoice_id=invoice_id,
            triggering_action=triggering_action,
            correlation_id=correlation_id,
            idempotency_key=idempotency_key,
        )
        return self.credit_check_repository.add(session, credit_check)