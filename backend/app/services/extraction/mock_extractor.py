import json
from typing import Optional
from app.schemas.invoice_extraction import ExtractedInvoice, ExtractedLineItem
from app.services.extraction.base import IExtractionService


class MockExtractor(IExtractionService):
    def __init__(self, override_result: Optional[ExtractedInvoice] = None):
        self.override_result = override_result

    async def extract_invoice(
        self,
        pdf_bytes: bytes,
        filename: Optional[str] = None,
    ) -> ExtractedInvoice:
        if self.override_result:
            return self.override_result

        # Check if pdf_bytes contains an embedded mock payload
        marker = b"LEDGERPILOT_MOCK_DATA:"
        if marker in pdf_bytes:
            try:
                start = pdf_bytes.find(marker) + len(marker)
                end = pdf_bytes.find(b"\n", start)
                if end == -1:
                    raw_json = pdf_bytes[start:].decode("utf-8", errors="ignore").strip()
                else:
                    raw_json = pdf_bytes[start:end].decode("utf-8", errors="ignore").strip()
                data = json.loads(raw_json)
                return ExtractedInvoice(**data)
            except Exception:
                pass

        # Default deterministic test extraction
        return ExtractedInvoice(
            invoice_number="INV-2026-001",
            vendor_name="Apex Hardware Supplies LLC",
            vendor_tax_id="US-XX9912041",
            vendor_address="100 Industrial Parkway, Austin, TX 78701",
            invoice_date="2026-10-02",
            due_date="2026-11-01",
            purchase_order_number="PO-2026-0089",
            currency="USD",
            line_items=[
                ExtractedLineItem(
                    line_number=1,
                    description="Industrial Grade Steel Bolts M12",
                    quantity=500.0,
                    unit_price=3.0,
                    total_amount=1500.0,
                    po_line_reference="PO-2026-0089-1",
                ),
            ],
            subtotal=1500.0,
            tax_amount=120.0,
            total_amount=1620.0,
            payment_terms="Net 30",
        )
