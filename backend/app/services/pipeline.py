import json
import logging
from sqlmodel import select
from app.db.session import async_session_factory
from app.models.invoice import Invoice, InvoiceStatus
from app.models.vendor import Vendor
from app.models.purchase_order import PurchaseOrder, POLineItem
from app.models.goods_receipt import GoodsReceipt, GoodsReceiptItem
from app.models.line_item import LineItem
from app.models.audit_log import AuditLog
from app.services.events.manager import event_broadcaster
from app.services.extraction.factory import get_extraction_service
from app.services.matching.matcher import ThreeWayMatcher
from app.services.matching.anomaly_detector import AnomalyDetector

logger = logging.getLogger(__name__)


async def run_reconciliation_pipeline(
    invoice_id: str,
    pdf_bytes: bytes,
    user_id: str,
) -> None:
    async with async_session_factory() as session:
        invoice = await session.get(Invoice, invoice_id)
        if not invoice:
            logger.error("Invoice %s not found for pipeline processing", invoice_id)
            return

        try:
            # Stage 1: EXTRACTING (20%)
            invoice.status = InvoiceStatus.EXTRACTING
            session.add(invoice)
            await session.commit()
            await event_broadcaster.publish(
                invoice_id=invoice_id,
                status=InvoiceStatus.EXTRACTING.value,
                progress=20,
                message="Rasterizing PDF and initiating vision extraction model...",
            )

            # Extract via Vision / Mock Service
            extractor = get_extraction_service()
            extracted = await extractor.extract_invoice(pdf_bytes)

            # Update invoice header fields
            invoice.invoice_number = extracted.invoice_number
            invoice.subtotal = extracted.subtotal
            invoice.tax_amount = extracted.tax_amount
            invoice.total_amount = extracted.total_amount
            invoice.currency = extracted.currency

            # Stage 2: MATCHING (50%)
            invoice.status = InvoiceStatus.MATCHING
            session.add(invoice)
            await session.commit()
            await event_broadcaster.publish(
                invoice_id=invoice_id,
                status=InvoiceStatus.MATCHING.value,
                progress=50,
                message=f"Extracted {len(extracted.line_items)} line items. Querying purchase orders and vendor master...",
            )

            # Lookup Vendor by name / tax ID for this user
            vendor_stmt = select(Vendor).where(
                Vendor.user_id == user_id,
                (Vendor.normalized_name == extracted.vendor_name.strip().lower())
                | (Vendor.name == extracted.vendor_name.strip()),
            )
            vendor_res = await session.exec(vendor_stmt)
            vendor = vendor_res.first()

            # If vendor doesn't exist, create an auto-registered vendor record
            if not vendor:
                vendor = Vendor(
                    user_id=user_id,
                    name=extracted.vendor_name,
                    normalized_name=extracted.vendor_name.strip().lower(),
                    tax_id=extracted.vendor_tax_id,
                    address=extracted.vendor_address,
                    payment_terms=extracted.payment_terms or "Net 30",
                )
                session.add(vendor)
                await session.commit()
                await session.refresh(vendor)

            invoice.vendor_id = vendor.id

            # Lookup PO if referenced
            po = None
            po_items = []
            grns = []
            grn_items = []

            if extracted.purchase_order_number:
                po_stmt = select(PurchaseOrder).where(
                    PurchaseOrder.user_id == user_id,
                    PurchaseOrder.po_number == extracted.purchase_order_number,
                )
                po_res = await session.exec(po_stmt)
                po = po_res.first()

                if po:
                    poi_stmt = select(POLineItem).where(POLineItem.purchase_order_id == po.id)
                    poi_res = await session.exec(poi_stmt)
                    po_items = list(poi_res.all())

                    grn_stmt = select(GoodsReceipt).where(GoodsReceipt.purchase_order_id == po.id)
                    grn_res = await session.exec(grn_stmt)
                    grns = list(grn_res.all())

                    if grns:
                        grn_ids = [g.id for g in grns]
                        gri_stmt = select(GoodsReceiptItem).where(GoodsReceiptItem.goods_receipt_id.in_(grn_ids))
                        gri_res = await session.exec(gri_stmt)
                        grn_items = list(gri_res.all())

            # Perform Three-Way Match
            matcher = ThreeWayMatcher()
            match_res = matcher.reconcile(
                invoice=extracted,
                vendor=vendor,
                po=po,
                po_items=po_items,
                goods_receipts=grns,
                grn_items=grn_items,
            )

            # Persist line items
            for line_res in match_res.line_results:
                line_obj = LineItem(
                    invoice_id=invoice.id,
                    line_number=line_res.line_number,
                    description=line_res.invoice_description,
                    quantity=line_res.invoice_qty,
                    unit_price=line_res.invoice_unit_price,
                    total_amount=line_res.invoice_total,
                    po_line_item_id=line_res.po_line_id,
                    match_status=line_res.match_status,
                    price_variance=line_res.price_variance_pct,
                    quantity_variance=line_res.quantity_variance_pct,
                    mismatch_reason=",".join([r.value for r in line_res.mismatch_reasons]) if line_res.mismatch_reasons else None,
                )
                session.add(line_obj)

            invoice.confidence_score = match_res.confidence_score

            # Stage 3: ANOMALY_CHECK (80%)
            invoice.status = InvoiceStatus.ANOMALY_CHECK
            session.add(invoice)
            await session.commit()
            await event_broadcaster.publish(
                invoice_id=invoice_id,
                status=InvoiceStatus.ANOMALY_CHECK.value,
                progress=80,
                message="Evaluating tax rates, duplicate hashes, and transaction risk...",
            )

            detector = AnomalyDetector()
            anomalies = await detector.detect_anomalies(
                session=session,
                user_id=user_id,
                vendor_id=vendor.id,
                invoice=extracted,
                current_invoice_id=invoice.id,
            )
            # Combine matcher anomalies with detector anomalies
            all_anomalies = match_res.anomalies + anomalies
            if all_anomalies:
                invoice.anomaly_flags = json.dumps(all_anomalies)

            # Stage 4: READY_FOR_REVIEW (100%)
            invoice.status = InvoiceStatus.READY_FOR_REVIEW
            session.add(invoice)

            # Create Audit Log
            audit = AuditLog(
                user_id=user_id,
                entity_type="INVOICE",
                entity_id=invoice.id,
                action="RECONCILED",
                actor_type="SYSTEM",
                previous_state=InvoiceStatus.UPLOADED.value,
                new_state=InvoiceStatus.READY_FOR_REVIEW.value,
                metadata_json=json.dumps({
                    "confidence_score": match_res.confidence_score,
                    "overall_status": match_res.overall_status.value,
                    "anomalies_count": len(all_anomalies),
                }),
            )
            session.add(audit)
            await session.commit()

            await event_broadcaster.publish(
                invoice_id=invoice_id,
                status=InvoiceStatus.READY_FOR_REVIEW.value,
                progress=100,
                message=f"Pipeline complete: {match_res.summary}",
            )

        except Exception as e:
            logger.exception("Pipeline failed for invoice %s: %s", invoice_id, e)
            invoice.status = InvoiceStatus.FAILED
            session.add(invoice)
            await session.commit()
            await event_broadcaster.publish(
                invoice_id=invoice_id,
                status=InvoiceStatus.FAILED.value,
                progress=100,
                message=f"Processing failed: {str(e)}",
                event_type="ERROR",
            )
