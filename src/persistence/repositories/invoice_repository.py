from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
import json

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.domain.models.invoice import (
    BLOCKED,
    Invoice,
    InvoiceMatchResult,
    MATCHED_CLEAN,
    MATCHED_WITH_WARNING,
    OpenLineExposure,
    OpenExposureWarning,
    OPEN_RECEIPT_EXPOSURE,
)
from src.persistence.models.invoice import InvoiceRow
from src.persistence.models.invoice_match_snapshot import InvoiceMatchSnapshotRow


UNPAID_STATUSES = ["PENDING", "MATCHED", "APPROVED"]


@dataclass(frozen=True)
class ExposureAggregate:
    as_of_timestamp: datetime
    outstanding_total_amount: Decimal
    open_invoice_count: int
    included_invoice_statuses: list[str]


class InvoiceRepository:
    def get_by_id(self, session: Session, invoice_id: str) -> Invoice | None:
        row = session.get(InvoiceRow, invoice_id)
        return self._to_domain(row) if row is not None else None

    def get_by_vendor_and_invoice_number(
        self,
        session: Session,
        vendor_id: str,
        invoice_number: str,
    ) -> Invoice | None:
        stmt = (
            select(InvoiceRow)
            .where(InvoiceRow.vendor_id == vendor_id)
            .where(InvoiceRow.invoice_number == invoice_number)
        )
        row = session.execute(stmt).scalar_one_or_none()
        return self._to_domain(row) if row is not None else None

    def add(self, session: Session, invoice: Invoice) -> Invoice:
        session.add(
            InvoiceRow(
                id=invoice.id,
                vendor_id=invoice.vendor_id,
                po_id=invoice.purchase_order_id,
                invoice_number=invoice.invoice_number,
                amount=invoice.invoice_amount,
                status=invoice.status,
                last_match_outcome=invoice.last_match_outcome,
                created_at=invoice.created_at,
                matched_at=invoice.matched_at,
            )
        )
        session.flush()
        return invoice

    def update(self, session: Session, invoice: Invoice) -> Invoice:
        row = session.get(InvoiceRow, invoice.id)
        if row is None:
            raise ValueError(f"Invoice {invoice.id} not found for update.")
        row.status = invoice.status
        row.last_match_outcome = invoice.last_match_outcome
        row.matched_at = invoice.matched_at
        session.flush()
        return invoice

    def add_match_snapshot(self, session: Session, match_result: InvoiceMatchResult) -> InvoiceMatchResult:
        session.add(
            InvoiceMatchSnapshotRow(
                id=match_result.snapshot_id,
                invoice_id=match_result.invoice_id,
                idempotency_key=match_result.idempotency_key or "",
                outcome=match_result.match_status,
                invoice_amount=match_result.invoice_amount,
                received_value=match_result.received_value,
                ordered_value=match_result.ordered_value,
                difference_amount=match_result.difference_amount,
                shortfall_amount=match_result.shortfall_amount,
                next_action=match_result.next_action,
                all_lines_fully_received=match_result.all_lines_fully_received,
                warning_code=match_result.warning.code if match_result.warning is not None else None,
                remaining_order_value=match_result.remaining_order_value,
                purchase_order_status=match_result.purchase_order_status,
                open_lines_json=json.dumps(
                    [
                        {
                            "po_line_item_id": line.po_line_item_id,
                            "sku": line.sku,
                            "qty_remaining": line.qty_remaining,
                            "remaining_value": format(line.remaining_value, "f"),
                        }
                        for line in match_result.open_lines
                    ],
                    separators=(",", ":"),
                    ensure_ascii=True,
                ),
                evaluated_at=match_result.evaluated_at,
                matched_at=match_result.matched_at,
            )
        )
        session.flush()
        return match_result

    def get_match_snapshot_by_id(self, session: Session, snapshot_id: str) -> InvoiceMatchResult | None:
        row = session.get(InvoiceMatchSnapshotRow, snapshot_id)
        if row is None:
            return None
        open_lines = [
            OpenLineExposure(
                po_line_item_id=item["po_line_item_id"],
                sku=item["sku"],
                qty_remaining=item["qty_remaining"],
                remaining_value=Decimal(item["remaining_value"]).quantize(Decimal("0.01")),
            )
            for item in json.loads(row.open_lines_json)
        ]
        warning = None
        if row.warning_code == OPEN_RECEIPT_EXPOSURE:
            warning = OpenExposureWarning(
                code=OPEN_RECEIPT_EXPOSURE,
                message="Purchase order still has open receipt exposure.",
                exposure_amount=Decimal(row.remaining_order_value).quantize(Decimal("0.01")),
                purchase_order_status=row.purchase_order_status,
                remaining_order_value=Decimal(row.remaining_order_value).quantize(Decimal("0.01")),
                open_lines=open_lines,
            )
        invoice_status = "PENDING" if row.outcome == BLOCKED else "MATCHED"
        return InvoiceMatchResult(
            snapshot_id=row.id,
            invoice_id=row.invoice_id,
            purchase_order_id=self._get_purchase_order_id(session, row.invoice_id),
            invoice_status=invoice_status,
            last_match_outcome=row.outcome,
            match_status=row.outcome,
            invoice_amount=Decimal(row.invoice_amount).quantize(Decimal("0.01")),
            received_value=Decimal(row.received_value).quantize(Decimal("0.01")),
            ordered_value=Decimal(row.ordered_value).quantize(Decimal("0.01")),
            difference_amount=Decimal(row.difference_amount).quantize(Decimal("0.01")),
            remaining_order_value=Decimal(row.remaining_order_value).quantize(Decimal("0.01")),
            all_lines_fully_received=row.all_lines_fully_received,
            open_lines=open_lines,
            next_action=row.next_action,
            evaluated_at=row.evaluated_at,
            purchase_order_status=row.purchase_order_status,
            matched_at=row.matched_at,
            shortfall_amount=(Decimal(row.shortfall_amount).quantize(Decimal("0.01")) if row.shortfall_amount is not None else None),
            warning=warning,
            idempotency_key=row.idempotency_key,
        )

    def get_exposure_aggregate(self, session: Session, vendor_id: str) -> ExposureAggregate:
        stmt = (
            select(
                func.coalesce(func.sum(InvoiceRow.amount), 0),
                func.count(InvoiceRow.id),
            )
            .where(InvoiceRow.vendor_id == vendor_id)
            .where(InvoiceRow.status.in_(UNPAID_STATUSES))
        )
        total, count = session.execute(stmt).one()
        normalized_total = Decimal(total).quantize(Decimal("0.01")) if not isinstance(total, Decimal) else total.quantize(Decimal("0.01"))
        return ExposureAggregate(
            as_of_timestamp=datetime.now(UTC),
            outstanding_total_amount=normalized_total,
            open_invoice_count=count,
            included_invoice_statuses=list(UNPAID_STATUSES),
        )

    @staticmethod
    def _to_domain(row: InvoiceRow) -> Invoice:
        return Invoice(
            id=row.id,
            vendor_id=row.vendor_id,
            purchase_order_id=row.po_id,
            invoice_number=row.invoice_number,
            invoice_amount=Decimal(row.amount).quantize(Decimal("0.01")),
            status=row.status,
            last_match_outcome=row.last_match_outcome,
            created_at=row.created_at,
            matched_at=row.matched_at,
        )

    @staticmethod
    def _get_purchase_order_id(session: Session, invoice_id: str) -> str:
        stmt = select(InvoiceRow.po_id).where(InvoiceRow.id == invoice_id)
        purchase_order_id = session.execute(stmt).scalar_one()
        return purchase_order_id

