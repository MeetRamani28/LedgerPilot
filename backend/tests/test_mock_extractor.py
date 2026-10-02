import pytest
from PIL import Image
from app.services.extraction.mock_extractor import MockExtractor
from app.services.extraction.factory import get_extraction_service
from app.services.extraction.pdf_utils import image_to_base64
from app.schemas.invoice_extraction import ExtractedInvoice, ExtractedLineItem


@pytest.mark.anyio
async def test_mock_extractor_default():
    extractor = MockExtractor()
    result = await extractor.extract_invoice(pdf_bytes=b"%PDF-1.4 dummy bytes")

    assert isinstance(result, ExtractedInvoice)
    assert result.invoice_number == "INV-2026-001"
    assert result.vendor_name == "Apex Hardware Supplies LLC"
    assert len(result.line_items) == 1
    assert result.subtotal == 1500.0
    assert result.total_amount == 1620.0


@pytest.mark.anyio
async def test_mock_extractor_override():
    custom_invoice = ExtractedInvoice(
        invoice_number="INV-CUSTOM-999",
        vendor_name="Custom Vendor Inc",
        line_items=[
            ExtractedLineItem(
                line_number=1,
                description="Custom Service",
                quantity=1.0,
                unit_price=250.0,
                total_amount=250.0,
            )
        ],
        subtotal=250.0,
        tax_amount=25.0,
        total_amount=275.0,
    )
    extractor = MockExtractor(override_result=custom_invoice)
    result = await extractor.extract_invoice(pdf_bytes=b"dummy")

    assert result.invoice_number == "INV-CUSTOM-999"
    assert result.total_amount == 275.0


def test_factory_returns_mock_extractor():
    service = get_extraction_service("mock")
    assert isinstance(service, MockExtractor)


def test_image_to_base64():
    # Create simple 10x10 RGB test image
    img = Image.new("RGB", (10, 10), color="blue")
    b64_str = image_to_base64(img, format="JPEG")
    assert isinstance(b64_str, str)
    assert len(b64_str) > 10
