import math
from typing import Optional
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from app.models.invoice import Invoice
from app.schemas.invoice_extraction import ExtractedInvoice
from app.services.matching.tolerance_config import ToleranceConfig


class AnomalyDetector:
    def __init__(self, tolerance: Optional[ToleranceConfig] = None):
        self.tolerance = tolerance or ToleranceConfig()

    async def check_duplicate_invoice(
        self,
        session: AsyncSession,
        user_id: str,
        vendor_id: Optional[str],
        invoice_number: str,
        current_invoice_id: Optional[str] = None,
    ) -> Optional[str]:
        """Check if an invoice with the same invoice number for this vendor already exists."""
        if not vendor_id:
            return None

        statement = select(Invoice).where(
            Invoice.user_id == user_id,
            Invoice.vendor_id == vendor_id,
            Invoice.invoice_number == invoice_number,
        )
        if current_invoice_id:
            statement = statement.where(Invoice.id != current_invoice_id)

        result = await session.exec(statement)
        existing = result.first()
        if existing:
            return f"Duplicate invoice detected: Invoice '{invoice_number}' already exists in system (ID: {existing.id})."
        return None

    def check_tax_anomaly(self, invoice: ExtractedInvoice) -> Optional[str]:
        """Flag tax amounts that exceed standard thresholds or are mathematically abnormal."""
        if invoice.subtotal <= 0:
            return None

        tax_rate = invoice.tax_amount / invoice.subtotal
        if tax_rate > self.tolerance.tax_rate_max_pct:
            return (
                f"Suspiciously high tax rate ({tax_rate * 100:.1f}%) detected on invoice; "
                f"exceeds standard threshold of {self.tolerance.tax_rate_max_pct * 100:.0f}%."
            )
        if invoice.tax_amount < 0:
            return f"Negative tax amount ({invoice.tax_amount}) detected on invoice."
        return None

    def check_round_number_anomaly(self, invoice: ExtractedInvoice) -> Optional[str]:
        """Flag large invoices with suspiciously round totals (common fraud signature)."""
        if invoice.total_amount >= self.tolerance.round_number_threshold:
            # Check if total has zero cents and is a multiple of 1,000
            if math.isclose(invoice.total_amount % 1000.0, 0.0, abs_tol=0.001):
                return (
                    f"Round number anomaly: High-value transaction (${invoice.total_amount:,.2f}) "
                    f"is an exact thousand without cents."
                )
        return None

    async def detect_anomalies(
        self,
        session: AsyncSession,
        user_id: str,
        vendor_id: Optional[str],
        invoice: ExtractedInvoice,
        current_invoice_id: Optional[str] = None,
    ) -> list[str]:
        anomalies: list[str] = []

        # 1. Duplicate check
        dup_flag = await self.check_duplicate_invoice(
            session=session,
            user_id=user_id,
            vendor_id=vendor_id,
            invoice_number=invoice.invoice_number,
            current_invoice_id=current_invoice_id,
        )
        if dup_flag:
            anomalies.append(dup_flag)

        # 2. Tax anomaly check
        tax_flag = self.check_tax_anomaly(invoice)
        if tax_flag:
            anomalies.append(tax_flag)

        # 3. Round number anomaly check
        round_flag = self.check_round_number_anomaly(invoice)
        if round_flag:
            anomalies.append(round_flag)

        return anomalies
