import pytest
from pydantic import ValidationError
from app.schemas.invoice_extraction import ExtractedInvoice, ExtractedLineItem


def test_valid_invoice_schema():
    payload = {
        "invoice_number": "INV-2026-001",
        "vendor_name": "Apex Hardware Supplies LLC",
        "vendor_tax_id": "US-XX9912041",
        "currency": "USD",
        "line_items": [
            {
                "line_number": 1,
                "description": "Industrial Grade Steel Bolts M12",
                "quantity": 500.0,
                "unit_price": 3.0,
                "total_amount": 1500.0,
            },
            {
                "line_number": 2,
                "description": "Heavy Duty Washers",
                "quantity": 100.0,
                "unit_price": 1.5,
                "total_amount": 150.0,
            }
        ],
        "subtotal": 1650.0,
        "tax_amount": 132.0,
        "total_amount": 1782.0,
        "payment_terms": "Net 30",
    }

    invoice = ExtractedInvoice.model_validate(payload)
    assert invoice.invoice_number == "INV-2026-001"
    assert len(invoice.line_items) == 2
    assert invoice.total_amount == 1782.0


def test_line_item_math_mismatch():
    with pytest.raises(ValidationError) as exc_info:
        ExtractedLineItem(
            line_number=1,
            description="Steel Bolts",
            quantity=10.0,
            unit_price=5.0,
            total_amount=99.0,  # 10 * 5 = 50 != 99
        )
    assert "Line item math mismatch" in str(exc_info.value)


def test_subtotal_math_mismatch():
    payload = {
        "invoice_number": "INV-2026-002",
        "vendor_name": "Apex Hardware Supplies LLC",
        "line_items": [
            {
                "line_number": 1,
                "description": "Steel Bolts",
                "quantity": 10.0,
                "unit_price": 5.0,
                "total_amount": 50.0,
            }
        ],
        "subtotal": 100.0,  # Sum of line items is 50, but subtotal claimed 100
        "tax_amount": 5.0,
        "total_amount": 105.0,
    }
    with pytest.raises(ValidationError) as exc_info:
        ExtractedInvoice.model_validate(payload)
    assert "Sum of line items" in str(exc_info.value)


def test_grand_total_math_mismatch():
    payload = {
        "invoice_number": "INV-2026-003",
        "vendor_name": "Apex Hardware Supplies LLC",
        "line_items": [
            {
                "line_number": 1,
                "description": "Steel Bolts",
                "quantity": 10.0,
                "unit_price": 5.0,
                "total_amount": 50.0,
            }
        ],
        "subtotal": 50.0,
        "tax_amount": 5.0,
        "total_amount": 99.0,  # 50 + 5 = 55 != 99
    }
    with pytest.raises(ValidationError) as exc_info:
        ExtractedInvoice.model_validate(payload)
    assert "does not match total amount" in str(exc_info.value)


def test_empty_line_items_rejected():
    payload = {
        "invoice_number": "INV-2026-004",
        "vendor_name": "Apex Hardware Supplies LLC",
        "line_items": [],
        "subtotal": 0.0,
        "tax_amount": 0.0,
        "total_amount": 0.0,
    }
    with pytest.raises(ValidationError):
        ExtractedInvoice.model_validate(payload)
