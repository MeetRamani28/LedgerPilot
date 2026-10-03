import math
from typing import Optional
from app.models.vendor import Vendor
from app.models.purchase_order import PurchaseOrder, POLineItem
from app.models.goods_receipt import GoodsReceipt, GoodsReceiptItem
from app.models.line_item import MatchStatus
from app.schemas.invoice_extraction import ExtractedInvoice, ExtractedLineItem
from app.schemas.matching import (
    MatchResult,
    LineItemMatchResult,
    MismatchReasonCode,
)
from app.services.matching.tolerance_config import ToleranceConfig


class ThreeWayMatcher:
    def __init__(self, tolerance: Optional[ToleranceConfig] = None):
        self.tolerance = tolerance or ToleranceConfig()

    def reconcile(
        self,
        invoice: ExtractedInvoice,
        vendor: Optional[Vendor] = None,
        po: Optional[PurchaseOrder] = None,
        po_items: Optional[list[POLineItem]] = None,
        goods_receipts: Optional[list[GoodsReceipt]] = None,
        grn_items: Optional[list[GoodsReceiptItem]] = None,
    ) -> MatchResult:
        po_items = po_items or []
        goods_receipts = goods_receipts or []
        grn_items = grn_items or []

        anomalies: list[str] = []
        line_results: list[LineItemMatchResult] = []

        # 1. Vendor Validation
        if vendor is None:
            return MatchResult(
                overall_status=MatchStatus.UNMATCHED,
                confidence_score=0.0,
                is_matched=False,
                anomalies=["Vendor not recognized in vendor master."],
                summary=f"Unknown vendor: {invoice.vendor_name}",
            )

        # 2. Purchase Order Validation
        if po is None:
            return MatchResult(
                vendor_id=vendor.id,
                overall_status=MatchStatus.UNMATCHED,
                confidence_score=0.1,
                is_matched=False,
                anomalies=[f"Purchase order reference '{invoice.purchase_order_number}' not found."],
                summary=f"Missing PO: {invoice.purchase_order_number or 'None'}",
            )

        # Precompute received quantities per PO line item ID
        received_by_po_line: dict[str, float] = {}
        for gi in grn_items:
            received_by_po_line[gi.po_line_item_id] = (
                received_by_po_line.get(gi.po_line_item_id, 0.0) + gi.quantity_received
            )

        # 3. Line-Item Reconciliation
        unmatched_po_items = list(po_items)
        has_price_variance = False
        has_qty_discrepancy = False
        has_unmatched_lines = False

        for inv_line in invoice.line_items:
            best_match: Optional[POLineItem] = None
            best_match_idx: int = -1

            # Match by description (normalized case/substring)
            inv_desc = inv_line.description.strip().lower()
            for idx, poi in enumerate(unmatched_po_items):
                po_desc = poi.description.strip().lower()
                if inv_desc == po_desc or inv_desc in po_desc or po_desc in inv_desc:
                    best_match = poi
                    best_match_idx = idx
                    break

            if best_match is not None:
                unmatched_po_items.pop(best_match_idx)
                reasons: list[MismatchReasonCode] = []
                line_status = MatchStatus.MATCH

                # A. Unit Price Check
                po_unit_price = best_match.unit_price
                price_variance_pct = 0.0
                if po_unit_price > 0:
                    price_diff = abs(inv_line.unit_price - po_unit_price)
                    price_variance_pct = round(price_diff / po_unit_price, 4)
                    if price_variance_pct > self.tolerance.price_tolerance_pct:
                        reasons.append(MismatchReasonCode.PRICE_VARIANCE)
                        line_status = MatchStatus.PRICE_VARIANCE
                        has_price_variance = True

                # B. Quantity Check (against PO & Goods Receipt)
                po_qty = best_match.quantity
                received_qty = received_by_po_line.get(best_match.id, 0.0)
                qty_variance_pct = 0.0

                # Check if goods were received
                if received_qty == 0.0 and len(goods_receipts) == 0:
                    reasons.append(MismatchReasonCode.MISSING_GOODS_RECEIPT)
                    has_qty_discrepancy = True

                if po_qty > 0:
                    qty_diff = inv_line.quantity - po_qty
                    if qty_diff > 0:
                        qty_variance_pct = round(qty_diff / po_qty, 4)
                        if qty_variance_pct > self.tolerance.quantity_tolerance_pct:
                            reasons.append(MismatchReasonCode.QUANTITY_DISCREPANCY)
                            line_status = MatchStatus.QUANTITY_DISCREPANCY
                            has_qty_discrepancy = True
                
                # Check against Goods Receipt specifically
                if received_qty > 0 and inv_line.quantity > received_qty:
                    reasons.append(MismatchReasonCode.QUANTITY_DISCREPANCY)
                    line_status = MatchStatus.QUANTITY_DISCREPANCY
                    has_qty_discrepancy = True

                line_results.append(
                    LineItemMatchResult(
                        line_number=inv_line.line_number,
                        invoice_description=inv_line.description,
                        invoice_qty=inv_line.quantity,
                        invoice_unit_price=inv_line.unit_price,
                        invoice_total=inv_line.total_amount,
                        po_line_id=best_match.id,
                        po_sku=best_match.item_sku,
                        po_qty=best_match.quantity,
                        po_unit_price=best_match.unit_price,
                        received_qty=received_qty,
                        match_status=line_status,
                        price_variance_pct=price_variance_pct,
                        quantity_variance_pct=qty_variance_pct,
                        mismatch_reasons=reasons,
                    )
                )
            else:
                # Line could not be matched to any PO line item
                has_unmatched_lines = True
                line_results.append(
                    LineItemMatchResult(
                        line_number=inv_line.line_number,
                        invoice_description=inv_line.description,
                        invoice_qty=inv_line.quantity,
                        invoice_unit_price=inv_line.unit_price,
                        invoice_total=inv_line.total_amount,
                        match_status=MatchStatus.UNMATCHED,
                        mismatch_reasons=[MismatchReasonCode.LINE_ITEM_UNMATCHED],
                    )
                )

        # 4. Total Amount Variance Check
        # Compare invoice total, or subtotal when tax is itemized and PO total is pre-tax
        comp_total = invoice.total_amount
        if invoice.tax_amount > 0 and abs(invoice.subtotal - po.total_amount) < abs(invoice.total_amount - po.total_amount):
            comp_total = invoice.subtotal

        total_variance = round(abs(comp_total - po.total_amount), 2)
        if total_variance > self.tolerance.total_tolerance_abs:
            anomalies.append(
                f"Invoice total (${comp_total:.2f}) differs from PO total "
                f"(${po.total_amount:.2f}) by ${total_variance:.2f} (tolerance: ${self.tolerance.total_tolerance_abs:.2f})"
            )

        # 5. Determine Overall Match Status and Confidence Score
        confidence = 1.0

        if has_unmatched_lines:
            overall_status = MatchStatus.UNMATCHED
            confidence -= 0.4
        elif has_qty_discrepancy:
            overall_status = MatchStatus.QUANTITY_DISCREPANCY
            confidence -= 0.3
        elif has_price_variance:
            overall_status = MatchStatus.PRICE_VARIANCE
            confidence -= 0.2
        else:
            overall_status = MatchStatus.MATCH

        if total_variance > self.tolerance.total_tolerance_abs:
            confidence -= 0.15

        confidence = max(0.0, min(1.0, round(confidence, 2)))
        is_matched = overall_status == MatchStatus.MATCH and confidence >= 0.90

        summary = (
            f"3-Way Match Successful (100% confidence)"
            if is_matched
            else f"Reconciliation Flagged: {overall_status.value} (Confidence: {int(confidence * 100)}%)"
        )

        return MatchResult(
            vendor_id=vendor.id,
            po_id=po.id,
            overall_status=overall_status,
            confidence_score=confidence,
            is_matched=is_matched,
            line_results=line_results,
            anomalies=anomalies,
            total_variance=total_variance,
            summary=summary,
        )
