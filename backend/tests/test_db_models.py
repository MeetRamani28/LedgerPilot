import pytest
from datetime import date
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from app.models.vendor import Vendor
from app.models.invoice import Invoice, InvoiceStatus
from app.models.line_item import LineItem, MatchStatus
from app.models.purchase_order import PurchaseOrder, POLineItem, POStatus
from app.models.goods_receipt import GoodsReceipt, GoodsReceiptItem
from app.models.audit_log import AuditLog
from app.models.idempotency import IdempotencyKey
from app.db.repository import BaseRepository


@pytest.mark.anyio
async def test_database_models_lifecycle(test_session: AsyncSession):
    session = test_session
    user_id = "user_clerk_test_123"

    # 1. Create Vendor via Repository
    vendor_repo = BaseRepository(Vendor, session)
    vendor = Vendor(
        user_id=user_id,
        name="Apex Hardware Supplies LLC",
        normalized_name="apex hardware supplies llc",
        tax_id="US-XX9912041",
        contact_email="billing@apexhardware.com",
        payment_terms="Net 30",
    )
    created_vendor = await vendor_repo.create(vendor)
    assert created_vendor.id is not None
    assert created_vendor.created_at is not None

    # 2. Create Purchase Order & Line Item
    po = PurchaseOrder(
        user_id=user_id,
        vendor_id=created_vendor.id,
        po_number="PO-2026-0089",
        order_date=date(2026, 10, 1),
        total_amount=1500.0,
        status=POStatus.OPEN,
    )
    session.add(po)
    await session.commit()
    await session.refresh(po)

    po_item = POLineItem(
        purchase_order_id=po.id,
        line_number=1,
        item_sku="SKU-BOLT-100",
        description="Industrial Grade Steel Bolts M12",
        quantity=500.0,
        unit_price=3.0,
        total_amount=1500.0,
        quantity_received=0.0,
    )
    session.add(po_item)
    await session.commit()
    await session.refresh(po_item)
    assert po_item.id is not None

    # 3. Create Goods Receipt
    grn = GoodsReceipt(
        user_id=user_id,
        purchase_order_id=po.id,
        grn_number="GRN-2026-0044",
        receipt_date=date(2026, 10, 2),
        received_by="Warehouse Manager",
    )
    session.add(grn)
    await session.commit()
    await session.refresh(grn)

    grn_item = GoodsReceiptItem(
        goods_receipt_id=grn.id,
        po_line_item_id=po_item.id,
        item_sku="SKU-BOLT-100",
        quantity_received=500.0,
        condition="EXCELLENT",
    )
    session.add(grn_item)
    await session.commit()
    await session.refresh(grn_item)

    # 4. Create Invoice & Line Item
    invoice = Invoice(
        user_id=user_id,
        vendor_id=created_vendor.id,
        invoice_number="INV-APEX-8901",
        invoice_date=date(2026, 10, 2),
        due_date=date(2026, 11, 1),
        subtotal=1500.0,
        tax_amount=120.0,
        total_amount=1620.0,
        status=InvoiceStatus.UPLOADED,
        file_url="/uploads/inv_apex_8901.pdf",
        storage_key="uploads/inv_apex_8901.pdf",
        file_hash="sha256_placeholder_hash_12345",
    )
    session.add(invoice)
    await session.commit()
    await session.refresh(invoice)

    line_item = LineItem(
        invoice_id=invoice.id,
        line_number=1,
        description="Industrial Grade Steel Bolts M12",
        quantity=500.0,
        unit_price=3.0,
        total_amount=1500.0,
        po_line_item_id=po_item.id,
        match_status=MatchStatus.MATCH,
    )
    session.add(line_item)
    await session.commit()

    # 5. Create Audit Log
    audit = AuditLog(
        user_id=user_id,
        entity_type="INVOICE",
        entity_id=invoice.id,
        action="CREATED",
        actor_type="USER",
        actor_id=user_id,
        new_state=InvoiceStatus.UPLOADED.value,
    )
    session.add(audit)
    await session.commit()

    # 6. Create Idempotency Key
    idemp = IdempotencyKey(
        key="idemp_hash_apex_8901",
        user_id=user_id,
        request_hash="sha256_request_hash_987",
        status_code=200,
        response_body='{"invoice_id": "created"}',
    )
    session.add(idemp)
    await session.commit()

    # 7. Verify Queries
    result = await session.exec(select(Invoice).where(Invoice.user_id == user_id))
    invoices = result.all()
    assert len(invoices) >= 1
    assert invoices[0].invoice_number == "INV-APEX-8901"
    assert invoices[0].status == InvoiceStatus.UPLOADED

    # Test repository list and get
    all_vendors = await vendor_repo.list()
    assert len(all_vendors) == 1
    assert all_vendors[0].name == "Apex Hardware Supplies LLC"
