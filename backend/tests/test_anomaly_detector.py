import pytest
from datetime import date
from sqlmodel.ext.asyncio.session import AsyncSession
from app.models.invoice import Invoice, InvoiceStatus
from app.schemas.invoice_extraction import ExtractedInvoice, ExtractedLineItem
from app.services.matching.anomaly_detector import AnomalyDetector
from app.services.matching.tolerance_config import ToleranceConfig


@pytest.mark.anyio
async def test_duplicate_invoice_detection(test_session: AsyncSession):
    detector = AnomalyDetector()
    user_id = "user_anomaly_test"
    vendor_id = "vendor_test_1"

    # Pre-insert existing invoice into DB
    existing_inv = Invoice(
        user_id=user_id,
        vendor_id=vendor_id,
        invoice_number="INV-DUP-100",
        invoice_date=date(2026, 10, 1),
        subtotal=500.0,
        tax_amount=50.0,
        total_amount=550.0,
        status=InvoiceStatus.READY_FOR_REVIEW,
        file_url="/uploads/inv.pdf",
        storage_key="inv.pdf",
        file_hash="hash_123",
    )
    test_session.add(existing_inv)
    await test_session.commit()

    # Now check an incoming extracted invoice with identical invoice number
    incoming_invoice = ExtractedInvoice(
        invoice_number="INV-DUP-100",
        vendor_name="Apex Supplies",
        line_items=[
            ExtractedLineItem(
                line_number=1,
                description="Materials",
                quantity=1.0,
                unit_price=500.0,
                total_amount=500.0,
            )
        ],
        subtotal=500.0,
        tax_amount=50.0,
        total_amount=550.0,
    )

    anomalies = await detector.detect_anomalies(
        session=test_session,
        user_id=user_id,
        vendor_id=vendor_id,
        invoice=incoming_invoice,
    )

    assert len(anomalies) >= 1
    assert any("Duplicate invoice detected" in a for a in anomalies)


def test_high_tax_anomaly():
    detector = AnomalyDetector(tolerance=ToleranceConfig(tax_rate_max_pct=0.25))

    # 40% tax rate ($200 on $500 subtotal)
    invoice = ExtractedInvoice(
        invoice_number="INV-TAX-99",
        vendor_name="Apex Supplies",
        line_items=[
            ExtractedLineItem(
                line_number=1,
                description="Items",
                quantity=1.0,
                unit_price=500.0,
                total_amount=500.0,
            )
        ],
        subtotal=500.0,
        tax_amount=200.0,
        total_amount=700.0,
    )

    tax_flag = detector.check_tax_anomaly(invoice)
    assert tax_flag is not None
    assert "Suspiciously high tax rate" in tax_flag


def test_round_number_fraud_anomaly():
    detector = AnomalyDetector(tolerance=ToleranceConfig(round_number_threshold=10000.0))

    # Exactly $50,000.00
    invoice = ExtractedInvoice(
        invoice_number="INV-ROUND-01",
        vendor_name="Consulting Agency",
        line_items=[
            ExtractedLineItem(
                line_number=1,
                description="Consulting Retainer",
                quantity=1.0,
                unit_price=50000.0,
                total_amount=50000.0,
            )
        ],
        subtotal=50000.0,
        tax_amount=0.0,
        total_amount=50000.0,
    )

    round_flag = detector.check_round_number_anomaly(invoice)
    assert round_flag is not None
    assert "Round number anomaly" in round_flag
