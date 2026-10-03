import io
import json
import uuid
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.db.session import init_db, async_session_factory
from app.db.seed import seed_database
from tests.fixtures.sample_invoices import (
    generate_happy_path_invoice,
    generate_price_drift_invoice,
    generate_quantity_mismatch_invoice,
    generate_duplicate_invoice,
)


@pytest.fixture(autouse=True)
async def setup_db():
    await init_db()


@pytest.mark.anyio
async def test_e2e_happy_path_three_way_match():
    user_id = f"user_hp_{uuid.uuid4().hex}"
    auth_headers = {"Authorization": f"Bearer test_token_{user_id}"}

    async with async_session_factory() as session:
        await seed_database(session, user_id=user_id)

    pdf_bytes, meta = generate_happy_path_invoice()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        files = {"file": ("happy_path_invoice.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
        upload_res = await ac.post("/api/v1/invoices/upload", headers=auth_headers, files=files)
        assert upload_res.status_code == 201
        invoice_id = upload_res.json()["invoice_id"]

        # Fetch details
        detail_res = await ac.get(f"/api/v1/invoices/{invoice_id}", headers=auth_headers)
        assert detail_res.status_code == 200
        data = detail_res.json()
        invoice = data["invoice"]
        line_items = data["line_items"]

        assert invoice["status"] == "READY_FOR_REVIEW"
        assert invoice["invoice_number"] == "INV-HP-1001"
        assert invoice["confidence_score"] == 1.0
        assert invoice["anomaly_flags"] is None
        assert len(line_items) == 2
        for item in line_items:
            assert item["match_status"] == "MATCH"
            assert item["price_variance"] == 0.0
            assert item["quantity_variance"] == 0.0

        # Approve invoice
        approve_res = await ac.post(f"/api/v1/invoices/{invoice_id}/approve", headers=auth_headers)
        assert approve_res.status_code == 200
        assert approve_res.json()["status"] == "APPROVED"


@pytest.mark.anyio
async def test_e2e_price_drift_exceeding_tolerance():
    user_id = f"user_pd_{uuid.uuid4().hex}"
    auth_headers = {"Authorization": f"Bearer test_token_{user_id}"}

    async with async_session_factory() as session:
        await seed_database(session, user_id=user_id)

    pdf_bytes, meta = generate_price_drift_invoice()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        files = {"file": ("price_drift_invoice.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
        upload_res = await ac.post("/api/v1/invoices/upload", headers=auth_headers, files=files)
        assert upload_res.status_code == 201
        invoice_id = upload_res.json()["invoice_id"]

        detail_res = await ac.get(f"/api/v1/invoices/{invoice_id}", headers=auth_headers)
        assert detail_res.status_code == 200
        data = detail_res.json()
        invoice = data["invoice"]
        line_items = data["line_items"]

        assert invoice["status"] == "READY_FOR_REVIEW"
        assert invoice["confidence_score"] < 1.0
        assert len(line_items) == 1
        item = line_items[0]
        assert item["match_status"] == "PRICE_VARIANCE"
        assert item["price_variance"] > 0.05
        assert "PRICE_VARIANCE" in (item["mismatch_reason"] or "")


@pytest.mark.anyio
async def test_e2e_quantity_mismatch_exceeding_po_and_grn():
    user_id = f"user_qm_{uuid.uuid4().hex}"
    auth_headers = {"Authorization": f"Bearer test_token_{user_id}"}

    async with async_session_factory() as session:
        await seed_database(session, user_id=user_id)

    pdf_bytes, meta = generate_quantity_mismatch_invoice()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        files = {"file": ("quantity_mismatch_invoice.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
        upload_res = await ac.post("/api/v1/invoices/upload", headers=auth_headers, files=files)
        assert upload_res.status_code == 201
        invoice_id = upload_res.json()["invoice_id"]

        detail_res = await ac.get(f"/api/v1/invoices/{invoice_id}", headers=auth_headers)
        assert detail_res.status_code == 200
        data = detail_res.json()
        invoice = data["invoice"]
        line_items = data["line_items"]

        assert invoice["status"] == "READY_FOR_REVIEW"
        assert invoice["confidence_score"] < 1.0
        assert len(line_items) == 1
        item = line_items[0]
        assert item["match_status"] == "QUANTITY_DISCREPANCY"
        assert item["quantity_variance"] > 0.0
        assert "QUANTITY_DISCREPANCY" in (item["mismatch_reason"] or "")


@pytest.mark.anyio
async def test_e2e_duplicate_invoice_anomaly_and_hash_deduplication():
    user_id = f"user_dup_{uuid.uuid4().hex}"
    auth_headers = {"Authorization": f"Bearer test_token_{user_id}"}

    async with async_session_factory() as session:
        await seed_database(session, user_id=user_id)

    pdf_bytes, meta = generate_duplicate_invoice(salt="salt_attempt_1")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # First upload: new file hash, but duplicate invoice number from same vendor
        files = {"file": ("duplicate_invoice.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
        upload_res = await ac.post("/api/v1/invoices/upload", headers=auth_headers, files=files)
        assert upload_res.status_code == 201
        invoice_id = upload_res.json()["invoice_id"]

        detail_res = await ac.get(f"/api/v1/invoices/{invoice_id}", headers=auth_headers)
        assert detail_res.status_code == 200
        data = detail_res.json()
        invoice = data["invoice"]

        assert invoice["status"] == "READY_FOR_REVIEW"
        assert invoice["anomaly_flags"] is not None
        anomalies = json.loads(invoice["anomaly_flags"])
        assert any("Duplicate invoice detected" in a for a in anomalies)

        # Second upload: EXACT same file bytes -> caught at API file hash level
        files_repeat = {"file": ("duplicate_invoice.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
        repeat_res = await ac.post("/api/v1/invoices/upload", headers=auth_headers, files=files_repeat)
        assert repeat_res.status_code in (200, 201)
        repeat_data = repeat_res.json()
        assert repeat_data["is_duplicate"] is True
        assert repeat_data["invoice_id"] == invoice_id
