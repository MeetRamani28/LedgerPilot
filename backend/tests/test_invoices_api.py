import io
import uuid
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.db.session import init_db


@pytest.fixture(autouse=True)
async def ensure_db():
    await init_db()


@pytest.mark.anyio
async def test_unauthenticated_request_rejected():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/invoices/")
        assert response.status_code == 401


@pytest.mark.anyio
async def test_upload_invoice_lifecycle():
    unique_run = uuid.uuid4().hex
    auth_headers = {"Authorization": f"Bearer test_token_user_{unique_run}"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Upload valid PDF with unique byte payload
        dummy_pdf = io.BytesIO(f"%PDF-1.4 test payload {unique_run}".encode())
        files = {"file": (f"test_inv_{unique_run}.pdf", dummy_pdf, "application/pdf")}
        upload_res = await ac.post(
            "/api/v1/invoices/upload",
            headers=auth_headers,
            files=files,
        )
        assert upload_res.status_code == 201
        data = upload_res.json()
        assert "invoice_id" in data
        invoice_id = data["invoice_id"]
        assert data["status"] == "UPLOADED"

        # 2. List Invoices
        list_res = await ac.get("/api/v1/invoices/", headers=auth_headers)
        assert list_res.status_code == 200
        invoices = list_res.json()
        assert len(invoices) >= 1
        assert any(inv["id"] == invoice_id for inv in invoices)

        # 3. Get Details
        detail_res = await ac.get(f"/api/v1/invoices/{invoice_id}", headers=auth_headers)
        assert detail_res.status_code == 200
        detail_data = detail_res.json()
        assert detail_data["invoice"]["id"] == invoice_id

        # 4. Approve Invoice
        approve_res = await ac.post(f"/api/v1/invoices/{invoice_id}/approve", headers=auth_headers)
        assert approve_res.status_code == 200
        assert approve_res.json()["status"] == "APPROVED"

        # 5. Reject with reason
        reject_res = await ac.post(
            f"/api/v1/invoices/{invoice_id}/reject",
            headers=auth_headers,
            json={"reason": "Incorrect billing address"},
        )
        assert reject_res.status_code == 200
        assert reject_res.json()["status"] == "REJECTED"


@pytest.mark.anyio
async def test_idempotency_key_header():
    unique_key = f"idemp_{uuid.uuid4().hex}"
    auth_headers = {
        "Authorization": f"Bearer test_token_user_idemp_{unique_key}",
        "Idempotency-Key": unique_key,
    }

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        dummy_pdf = io.BytesIO(f"%PDF-1.4 first attempt {unique_key}".encode())
        files = {"file": ("sample.pdf", dummy_pdf, "application/pdf")}

        # First request
        res1 = await ac.post("/api/v1/invoices/upload", headers=auth_headers, files=files)
        assert res1.status_code == 201
        inv1_id = res1.json()["invoice_id"]

        # Duplicate request with same Idempotency-Key
        dummy_pdf2 = io.BytesIO(f"%PDF-1.4 first attempt {unique_key}".encode())
        files2 = {"file": ("sample.pdf", dummy_pdf2, "application/pdf")}
        res2 = await ac.post("/api/v1/invoices/upload", headers=auth_headers, files=files2)
        assert res2.status_code == 201
        assert res2.json()["invoice_id"] == inv1_id
