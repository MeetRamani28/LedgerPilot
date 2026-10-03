import json
import uuid


def build_sample_pdf(title: str, mock_data: dict, salt: str = "") -> bytes:
    """Generates a valid PDF byte string with embedded mock extraction metadata."""
    json_str = json.dumps(mock_data)
    salt_val = salt or uuid.uuid4().hex
    stream_content = f"BT /F1 12 Tf 50 720 Td ({title} - ID: {salt_val}) Tj ET\n".encode("latin1")
    stream_len = len(stream_content)

    pdf = (
        b"%PDF-1.4\n"
        b"%LEDGERPILOT_MOCK_DATA:" + json_str.encode("utf-8") + b"\n"
        b"%SALT:" + salt_val.encode("utf-8") + b"\n"
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\nendobj\n"
        b"4 0 obj\n<< /Length " + str(stream_len).encode("ascii") + b" >>\nstream\n"
        + stream_content +
        b"endstream\nendobj\n"
        b"5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n"
        b"xref\n0 6\n"
        b"0000000000 65535 f \n"
        b"0000000009 00000 n \n"
        b"0000000058 00000 n \n"
        b"0000000115 00000 n \n"
        b"0000000244 00000 n \n"
        b"0000000337 00000 n \n"
        b"trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n418\n%%EOF\n"
    )
    return pdf


def generate_happy_path_invoice(salt: str = "") -> tuple[bytes, dict]:
    data = {
        "invoice_number": "INV-HP-1001",
        "vendor_name": "Acme Industrial Supplies Ltd",
        "vendor_tax_id": "US-987654321",
        "vendor_address": "123 Steel Works Blvd, Cleveland, OH 44101",
        "invoice_date": "2026-10-01",
        "due_date": "2026-10-31",
        "purchase_order_number": "PO-1001",
        "currency": "USD",
        "line_items": [
            {
                "line_number": 1,
                "description": "High-Tensile Steel Fasteners M10",
                "quantity": 100.0,
                "unit_price": 10.0,
                "total_amount": 1000.0,
            },
            {
                "line_number": 2,
                "description": "Heavy Duty Hex Nuts Grade 8",
                "quantity": 100.0,
                "unit_price": 5.0,
                "total_amount": 500.0,
            },
        ],
        "subtotal": 1500.0,
        "tax_amount": 120.0,
        "total_amount": 1620.0,
        "payment_terms": "Net 30",
    }
    pdf_bytes = build_sample_pdf("Invoice - Happy Path Match", data, salt=salt)
    return pdf_bytes, data


def generate_price_drift_invoice(salt: str = "") -> tuple[bytes, dict]:
    data = {
        "invoice_number": "INV-PD-1002",
        "vendor_name": "Acme Industrial Supplies Ltd",
        "vendor_tax_id": "US-987654321",
        "vendor_address": "123 Steel Works Blvd, Cleveland, OH 44101",
        "invoice_date": "2026-10-01",
        "due_date": "2026-10-31",
        "purchase_order_number": "PO-1002",
        "currency": "USD",
        "line_items": [
            {
                "line_number": 1,
                "description": "Hydraulic Pressure Valve 2-Way",
                "quantity": 20.0,
                "unit_price": 112.0,
                "total_amount": 2240.0,
            },
        ],
        "subtotal": 2240.0,
        "tax_amount": 179.20,
        "total_amount": 2419.20,
        "payment_terms": "Net 30",
    }
    pdf_bytes = build_sample_pdf("Invoice - Price Drift", data, salt=salt)
    return pdf_bytes, data


def generate_quantity_mismatch_invoice(salt: str = "") -> tuple[bytes, dict]:
    data = {
        "invoice_number": "INV-QM-1003",
        "vendor_name": "Nexus Cloud Computing Inc",
        "vendor_tax_id": "US-123456789",
        "vendor_address": "456 Silicon Way, San Jose, CA 95110",
        "invoice_date": "2026-10-01",
        "due_date": "2026-10-31",
        "purchase_order_number": "PO-1003",
        "currency": "USD",
        "line_items": [
            {
                "line_number": 1,
                "description": "Enterprise Server Rack Mount 42U",
                "quantity": 10.0,
                "unit_price": 1000.0,
                "total_amount": 10000.0,
            },
        ],
        "subtotal": 10000.0,
        "tax_amount": 800.0,
        "total_amount": 10800.0,
        "payment_terms": "Net 30",
    }
    pdf_bytes = build_sample_pdf("Invoice - Quantity Mismatch", data, salt=salt)
    return pdf_bytes, data


def generate_duplicate_invoice(salt: str = "") -> tuple[bytes, dict]:
    data = {
        "invoice_number": "INV-DUP-999",
        "vendor_name": "Global Logistics Corp",
        "vendor_tax_id": "US-554433221",
        "vendor_address": "789 Harbor Rd, Seattle, WA 98101",
        "invoice_date": "2026-10-01",
        "due_date": "2026-10-31",
        "purchase_order_number": "PO-1004",
        "currency": "USD",
        "line_items": [
            {
                "line_number": 1,
                "description": "Freight Container Haulage 40ft",
                "quantity": 1.0,
                "unit_price": 3500.0,
                "total_amount": 3500.0,
            },
        ],
        "subtotal": 3500.0,
        "tax_amount": 280.0,
        "total_amount": 3780.0,
        "payment_terms": "Net 30",
    }
    pdf_bytes = build_sample_pdf("Invoice - Duplicate Test", data, salt=salt)
    return pdf_bytes, data
