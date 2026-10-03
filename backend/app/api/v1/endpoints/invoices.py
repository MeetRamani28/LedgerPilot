import hashlib
import json
from typing import Optional
from fastapi import APIRouter, BackgroundTasks, Depends, File, Header, HTTPException, Response, UploadFile, status
from pydantic import BaseModel
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from app.core.auth import ClerkUser, get_current_user
from app.db.session import get_session
from app.models.invoice import Invoice, InvoiceStatus
from app.models.line_item import LineItem
from app.models.vendor import Vendor
from app.models.audit_log import AuditLog
from app.models.idempotency import IdempotencyKey
from app.services.storage.local_storage import LocalStorageService
from app.services.pipeline import run_reconciliation_pipeline

router = APIRouter(prefix="/invoices", tags=["Invoices"])
storage_service = LocalStorageService()


class RejectionRequest(BaseModel):
    reason: str


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_invoice(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    current_user: ClerkUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF documents are supported.",
        )

    file_bytes = await file.read()
    if len(file_bytes) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )

    file_hash = hashlib.sha256(file_bytes).hexdigest()

    # 1. Idempotency Check via explicit header or duplicate file hash
    if idempotency_key:
        idemp_stmt = select(IdempotencyKey).where(
            IdempotencyKey.key == idempotency_key,
            IdempotencyKey.user_id == current_user.user_id,
        )
        idemp_res = await session.exec(idemp_stmt)
        cached = idemp_res.first()
        if cached:
            return Response(
                content=cached.response_body,
                status_code=cached.status_code,
                media_type="application/json",
            )

    # Check if duplicate file hash already exists for this user
    hash_stmt = select(Invoice).where(
        Invoice.user_id == current_user.user_id,
        Invoice.file_hash == file_hash,
    )
    hash_res = await session.exec(hash_stmt)
    existing_invoice = hash_res.first()
    if existing_invoice:
        return {
            "message": "Duplicate invoice already registered",
            "invoice_id": existing_invoice.id,
            "status": existing_invoice.status.value,
            "is_duplicate": True,
        }

    # 2. Store file locally
    file_url, storage_key = await storage_service.upload(
        file_bytes=file_bytes,
        filename=file.filename,
    )

    # 3. Create initial Invoice record
    invoice = Invoice(
        user_id=current_user.user_id,
        invoice_number="PENDING_EXTRACTION",
        status=InvoiceStatus.UPLOADED,
        file_url=file_url,
        storage_key=storage_key,
        file_hash=file_hash,
    )
    session.add(invoice)
    await session.commit()
    await session.refresh(invoice)

    # 4. Create Audit Log
    audit = AuditLog(
        user_id=current_user.user_id,
        entity_type="INVOICE",
        entity_id=invoice.id,
        action="UPLOADED",
        actor_type="USER",
        actor_id=current_user.user_id,
        new_state=InvoiceStatus.UPLOADED.value,
        metadata_json=json.dumps({"filename": file.filename, "file_size": len(file_bytes)}),
    )
    session.add(audit)

    # Record idempotency key if provided
    if idempotency_key:
        response_payload = json.dumps({
            "message": "Invoice uploaded successfully",
            "invoice_id": invoice.id,
            "status": invoice.status.value,
        })
        idemp_rec = IdempotencyKey(
            key=idempotency_key,
            user_id=current_user.user_id,
            request_hash=file_hash,
            status_code=201,
            response_body=response_payload,
        )
        session.add(idemp_rec)

    await session.commit()

    # 5. Queue background autonomous pipeline
    background_tasks.add_task(
        run_reconciliation_pipeline,
        invoice_id=invoice.id,
        pdf_bytes=file_bytes,
        user_id=current_user.user_id,
    )

    return {
        "message": "Invoice uploaded successfully",
        "invoice_id": invoice.id,
        "status": invoice.status.value,
    }


@router.get("/")
async def list_invoices(
    skip: int = 0,
    limit: int = 50,
    current_user: ClerkUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    stmt = (
        select(Invoice)
        .where(Invoice.user_id == current_user.user_id)
        .order_by(Invoice.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await session.exec(stmt)
    invoices = result.all()
    return invoices


@router.get("/{invoice_id}")
async def get_invoice_details(
    invoice_id: str,
    current_user: ClerkUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    invoice = await session.get(Invoice, invoice_id)
    if not invoice or invoice.user_id != current_user.user_id:
        raise HTTPException(status_code=404, detail="Invoice not found")

    # Fetch line items
    line_stmt = select(LineItem).where(LineItem.invoice_id == invoice.id).order_by(LineItem.line_number)
    line_res = await session.exec(line_stmt)
    line_items = list(line_res.all())

    # Fetch vendor
    vendor = await session.get(Vendor, invoice.vendor_id) if invoice.vendor_id else None

    # Fetch audit logs
    audit_stmt = (
        select(AuditLog)
        .where(AuditLog.entity_id == invoice.id)
        .order_by(AuditLog.created_at.desc())
    )
    audit_res = await session.exec(audit_stmt)
    audits = list(audit_res.all())

    return {
        "invoice": invoice,
        "vendor": vendor,
        "line_items": line_items,
        "audit_logs": audits,
        "anomalies": json.loads(invoice.anomaly_flags) if invoice.anomaly_flags else [],
    }


@router.get("/file/{storage_key}")
async def get_invoice_file(
    storage_key: str,
    current_user: ClerkUser = Depends(get_current_user),
):
    try:
        content = await storage_service.download(storage_key)
        return Response(
            content=content,
            media_type="application/pdf",
            headers={"Content-Disposition": f"inline; filename={storage_key}"},
        )
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")


@router.post("/{invoice_id}/approve")
async def approve_invoice(
    invoice_id: str,
    current_user: ClerkUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    invoice = await session.get(Invoice, invoice_id)
    if not invoice or invoice.user_id != current_user.user_id:
        raise HTTPException(status_code=404, detail="Invoice not found")

    prev_status = invoice.status.value
    invoice.status = InvoiceStatus.APPROVED
    session.add(invoice)

    audit = AuditLog(
        user_id=current_user.user_id,
        entity_type="INVOICE",
        entity_id=invoice.id,
        action="APPROVED",
        actor_type="USER",
        actor_id=current_user.user_id,
        previous_state=prev_status,
        new_state=InvoiceStatus.APPROVED.value,
    )
    session.add(audit)
    await session.commit()

    return {"message": "Invoice approved successfully", "status": invoice.status.value}


@router.post("/{invoice_id}/reject")
async def reject_invoice(
    invoice_id: str,
    rejection: RejectionRequest,
    current_user: ClerkUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    invoice = await session.get(Invoice, invoice_id)
    if not invoice or invoice.user_id != current_user.user_id:
        raise HTTPException(status_code=404, detail="Invoice not found")

    prev_status = invoice.status.value
    invoice.status = InvoiceStatus.REJECTED
    invoice.rejection_reason = rejection.reason
    session.add(invoice)

    audit = AuditLog(
        user_id=current_user.user_id,
        entity_type="INVOICE",
        entity_id=invoice.id,
        action="REJECTED",
        actor_type="USER",
        actor_id=current_user.user_id,
        previous_state=prev_status,
        new_state=InvoiceStatus.REJECTED.value,
        metadata_json=json.dumps({"reason": rejection.reason}),
    )
    session.add(audit)
    await session.commit()

    return {"message": "Invoice rejected", "status": invoice.status.value, "reason": rejection.reason}


class LineItemUpdateRequest(BaseModel):
    description: Optional[str] = None
    quantity: Optional[float] = None
    unit_price: Optional[float] = None


@router.patch("/{invoice_id}/line-items/{line_item_id}")
async def update_line_item(
    invoice_id: str,
    line_item_id: str,
    update_data: LineItemUpdateRequest,
    current_user: ClerkUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    invoice = await session.get(Invoice, invoice_id)
    if not invoice or invoice.user_id != current_user.user_id:
        raise HTTPException(status_code=404, detail="Invoice not found")

    line_item = await session.get(LineItem, line_item_id)
    if not line_item or line_item.invoice_id != invoice.id:
        raise HTTPException(status_code=404, detail="Line item not found")

    if update_data.description is not None:
        line_item.description = update_data.description
    if update_data.quantity is not None:
        line_item.quantity = update_data.quantity
    if update_data.unit_price is not None:
        line_item.unit_price = update_data.unit_price

    line_item.total_amount = round(line_item.quantity * line_item.unit_price, 2)
    session.add(line_item)
    await session.commit()
    await session.refresh(line_item)

    # Recalculate invoice subtotal and grand total
    stmt = select(LineItem).where(LineItem.invoice_id == invoice.id)
    items_res = await session.exec(stmt)
    all_items = list(items_res.all())
    new_subtotal = round(sum(i.total_amount for i in all_items), 2)
    invoice.subtotal = new_subtotal
    invoice.total_amount = round(new_subtotal + invoice.tax_amount, 2)
    session.add(invoice)

    # Audit log entry
    audit = AuditLog(
        user_id=current_user.user_id,
        entity_type="LINE_ITEM",
        entity_id=line_item.id,
        action="UPDATED",
        actor_type="USER",
        actor_id=current_user.user_id,
        metadata_json=json.dumps({
            "line_number": line_item.line_number,
            "new_qty": line_item.quantity,
            "new_unit_price": line_item.unit_price,
            "new_total": line_item.total_amount,
        }),
    )
    session.add(audit)
    await session.commit()

    return {
        "message": "Line item updated",
        "line_item": line_item,
        "invoice_subtotal": invoice.subtotal,
        "invoice_total": invoice.total_amount,
    }

