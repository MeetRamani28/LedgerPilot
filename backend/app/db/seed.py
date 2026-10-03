import asyncio
import logging
from datetime import date
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from app.db.session import init_db, async_session_factory
from app.models.vendor import Vendor
from app.models.purchase_order import PurchaseOrder, POLineItem, POStatus
from app.models.goods_receipt import GoodsReceipt, GoodsReceiptItem
from app.models.invoice import Invoice, InvoiceStatus

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DEFAULT_SEED_USER_ID = "user_demo_ledgerpilot"


async def seed_database(session: AsyncSession, user_id: str = DEFAULT_SEED_USER_ID) -> dict:
    """Seeds synthetic test data (Vendors, POs, Goods Receipts, baseline Invoices) for a given tenant."""
    logger.info("Starting seed process for tenant user_id=%s...", user_id)

    # 1. Vendors
    vendors_data = [
        {
            "name": "Acme Industrial Supplies Ltd",
            "normalized_name": "acme industrial supplies ltd",
            "tax_id": "US-987654321",
            "address": "123 Steel Works Blvd, Cleveland, OH 44101",
            "contact_email": "billing@acmeindustrial.com",
            "payment_terms": "Net 30",
        },
        {
            "name": "Nexus Cloud Computing Inc",
            "normalized_name": "nexus cloud computing inc",
            "tax_id": "US-123456789",
            "address": "456 Silicon Way, San Jose, CA 95110",
            "contact_email": "accounts@nexuscloud.io",
            "payment_terms": "Net 30",
        },
        {
            "name": "Global Logistics Corp",
            "normalized_name": "global logistics corp",
            "tax_id": "US-554433221",
            "address": "789 Harbor Rd, Seattle, WA 98101",
            "contact_email": "finance@globallogistics.com",
            "payment_terms": "Net 30",
        },
    ]

    vendor_map: dict[str, Vendor] = {}
    for v_data in vendors_data:
        stmt = select(Vendor).where(
            Vendor.user_id == user_id,
            Vendor.normalized_name == v_data["normalized_name"],
        )
        res = await session.exec(stmt)
        vendor = res.first()
        if not vendor:
            vendor = Vendor(user_id=user_id, **v_data)
            session.add(vendor)
            await session.commit()
            await session.refresh(vendor)
            logger.info("Created Vendor: %s (%s)", vendor.name, vendor.id)
        vendor_map[vendor.name] = vendor

    # 2. Purchase Orders, Line Items, and Goods Receipts
    po_configs = [
        # PO-1001: For Happy Path 100% Match
        {
            "po_number": "PO-1001",
            "vendor_name": "Acme Industrial Supplies Ltd",
            "order_date": date(2026, 9, 15),
            "total_amount": 1500.0,
            "status": POStatus.OPEN,
            "items": [
                {
                    "line_number": 1,
                    "item_sku": "SKU-FAST-10",
                    "description": "High-Tensile Steel Fasteners M10",
                    "quantity": 100.0,
                    "unit_price": 10.0,
                    "total_amount": 1000.0,
                    "quantity_received": 100.0,
                },
                {
                    "line_number": 2,
                    "item_sku": "SKU-NUT-08",
                    "description": "Heavy Duty Hex Nuts Grade 8",
                    "quantity": 100.0,
                    "unit_price": 5.0,
                    "total_amount": 500.0,
                    "quantity_received": 100.0,
                },
            ],
            "grn": {
                "grn_number": "GRN-1001",
                "receipt_date": date(2026, 9, 20),
            },
        },
        # PO-1002: For Price Drift (>5% variance)
        {
            "po_number": "PO-1002",
            "vendor_name": "Acme Industrial Supplies Ltd",
            "order_date": date(2026, 9, 18),
            "total_amount": 2000.0,
            "status": POStatus.OPEN,
            "items": [
                {
                    "line_number": 1,
                    "item_sku": "SKU-VALVE-02",
                    "description": "Hydraulic Pressure Valve 2-Way",
                    "quantity": 20.0,
                    "unit_price": 100.0,
                    "total_amount": 2000.0,
                    "quantity_received": 20.0,
                },
            ],
            "grn": {
                "grn_number": "GRN-1002",
                "receipt_date": date(2026, 9, 22),
            },
        },
        # PO-1003: For Quantity Mismatch (Billed 10 vs PO 5)
        {
            "po_number": "PO-1003",
            "vendor_name": "Nexus Cloud Computing Inc",
            "order_date": date(2026, 9, 20),
            "total_amount": 5000.0,
            "status": POStatus.OPEN,
            "items": [
                {
                    "line_number": 1,
                    "item_sku": "SKU-RACK-42U",
                    "description": "Enterprise Server Rack Mount 42U",
                    "quantity": 5.0,
                    "unit_price": 1000.0,
                    "total_amount": 5000.0,
                    "quantity_received": 5.0,
                },
            ],
            "grn": {
                "grn_number": "GRN-1003",
                "receipt_date": date(2026, 9, 25),
            },
        },
        # PO-1004: For Duplicate Anomaly
        {
            "po_number": "PO-1004",
            "vendor_name": "Global Logistics Corp",
            "order_date": date(2026, 9, 25),
            "total_amount": 3500.0,
            "status": POStatus.COMPLETED,
            "items": [
                {
                    "line_number": 1,
                    "item_sku": "SKU-FREIGHT-40",
                    "description": "Freight Container Haulage 40ft",
                    "quantity": 1.0,
                    "unit_price": 3500.0,
                    "total_amount": 3500.0,
                    "quantity_received": 1.0,
                },
            ],
            "grn": {
                "grn_number": "GRN-1004",
                "receipt_date": date(2026, 9, 28),
            },
        },
    ]

    seeded_pos: list[PurchaseOrder] = []
    for cfg in po_configs:
        vendor = vendor_map[cfg["vendor_name"]]
        po_stmt = select(PurchaseOrder).where(
            PurchaseOrder.user_id == user_id,
            PurchaseOrder.po_number == cfg["po_number"],
        )
        po_res = await session.exec(po_stmt)
        po = po_res.first()
        if not po:
            po = PurchaseOrder(
                user_id=user_id,
                vendor_id=vendor.id,
                po_number=cfg["po_number"],
                order_date=cfg["order_date"],
                total_amount=cfg["total_amount"],
                status=cfg["status"],
            )
            session.add(po)
            await session.commit()
            await session.refresh(po)
            logger.info("Created PO: %s (%s)", po.po_number, po.id)

            po_line_items = []
            for item in cfg["items"]:
                pli = POLineItem(
                    purchase_order_id=po.id,
                    line_number=item["line_number"],
                    item_sku=item["item_sku"],
                    description=item["description"],
                    quantity=item["quantity"],
                    unit_price=item["unit_price"],
                    total_amount=item["total_amount"],
                    quantity_received=item["quantity_received"],
                )
                session.add(pli)
                po_line_items.append(pli)
            await session.commit()

            # Create Goods Receipt
            grn_cfg = cfg["grn"]
            grn = GoodsReceipt(
                user_id=user_id,
                purchase_order_id=po.id,
                grn_number=grn_cfg["grn_number"],
                receipt_date=grn_cfg["receipt_date"],
                received_by="Warehouse Receiver 1",
            )
            session.add(grn)
            await session.commit()
            await session.refresh(grn)

            # Refresh line items to get IDs
            for pli in po_line_items:
                await session.refresh(pli)
                gri = GoodsReceiptItem(
                    goods_receipt_id=grn.id,
                    po_line_item_id=pli.id,
                    item_sku=pli.item_sku,
                    quantity_received=pli.quantity_received,
                    condition="GOOD",
                )
                session.add(gri)
            await session.commit()
            logger.info("Created Goods Receipt: %s for PO: %s", grn.grn_number, po.po_number)
        seeded_pos.append(po)

    # 3. Baseline historical invoice for Duplicate Invoice test case (INV-DUP-999)
    dup_vendor = vendor_map["Global Logistics Corp"]
    dup_stmt = select(Invoice).where(
        Invoice.user_id == user_id,
        Invoice.invoice_number == "INV-DUP-999",
    )
    dup_res = await session.exec(dup_stmt)
    if not dup_res.first():
        baseline_invoice = Invoice(
            user_id=user_id,
            vendor_id=dup_vendor.id,
            invoice_number="INV-DUP-999",
            invoice_date=date(2026, 9, 29),
            due_date=date(2026, 10, 29),
            currency="USD",
            subtotal=3500.0,
            tax_amount=280.0,
            total_amount=3780.0,
            status=InvoiceStatus.APPROVED,
            file_url="/uploads/baseline_inv_dup_999.pdf",
            storage_key="seed_baseline_inv_dup_999",
            file_hash="hash_baseline_dup_999_preexisting",
            confidence_score=1.0,
        )
        session.add(baseline_invoice)
        await session.commit()
        logger.info("Created baseline historical invoice for duplicate test: INV-DUP-999")

    logger.info("Seed completed successfully!")
    return {
        "user_id": user_id,
        "vendors_count": len(vendor_map),
        "pos_count": len(seeded_pos),
    }


async def main():
    await init_db()
    async with async_session_factory() as session:
        result = await seed_database(session)
        print("Seed result:", result)


if __name__ == "__main__":
    asyncio.run(main())
