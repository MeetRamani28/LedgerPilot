from datetime import date
import pytest
from app.models.vendor import Vendor
from app.models.purchase_order import PurchaseOrder, POLineItem, POStatus
from app.models.goods_receipt import GoodsReceipt, GoodsReceiptItem
from app.models.line_item import MatchStatus
from app.schemas.invoice_extraction import ExtractedInvoice, ExtractedLineItem
from app.schemas.matching import MismatchReasonCode
from app.services.matching.matcher import ThreeWayMatcher
from app.services.matching.tolerance_config import ToleranceConfig


@pytest.fixture
def sample_vendor():
    return Vendor(
        id="v_apex_01",
        user_id="user_test",
        name="Apex Industrial Hardware",
        normalized_name="apex industrial hardware",
        tax_id="US-9912041",
    )


@pytest.fixture
def sample_po(sample_vendor):
    po = PurchaseOrder(
        id="po_100",
        user_id="user_test",
        vendor_id=sample_vendor.id,
        po_number="PO-2026-99",
        order_date=date(2026, 10, 1),
        total_amount=1000.0,
        status=POStatus.OPEN,
    )
    po_item = POLineItem(
        id="poi_1",
        purchase_order_id=po.id,
        line_number=1,
        item_sku="BOLT-M12",
        description="Industrial Grade Steel Bolts M12",
        quantity=100.0,
        unit_price=10.0,
        total_amount=1000.0,
        quantity_received=100.0,
    )
    return po, [po_item]


@pytest.fixture
def sample_grn(sample_po):
    po, po_items = sample_po
    grn = GoodsReceipt(
        id="grn_1",
        user_id="user_test",
        purchase_order_id=po.id,
        grn_number="GRN-55",
        receipt_date=date(2026, 10, 2),
    )
    grn_item = GoodsReceiptItem(
        id="gri_1",
        goods_receipt_id=grn.id,
        po_line_item_id=po_items[0].id,
        item_sku="BOLT-M12",
        quantity_received=100.0,
    )
    return [grn], [grn_item]


def test_exact_three_way_match(sample_vendor, sample_po, sample_grn):
    po, po_items = sample_po
    grns, grn_items = sample_grn
    matcher = ThreeWayMatcher()

    invoice = ExtractedInvoice(
        invoice_number="INV-001",
        vendor_name="Apex Industrial Hardware",
        purchase_order_number="PO-2026-99",
        line_items=[
            ExtractedLineItem(
                line_number=1,
                description="Industrial Grade Steel Bolts M12",
                quantity=100.0,
                unit_price=10.0,
                total_amount=1000.0,
            )
        ],
        subtotal=1000.0,
        tax_amount=0.0,
        total_amount=1000.0,
    )

    result = matcher.reconcile(
        invoice=invoice,
        vendor=sample_vendor,
        po=po,
        po_items=po_items,
        goods_receipts=grns,
        grn_items=grn_items,
    )

    assert result.is_matched is True
    assert result.overall_status == MatchStatus.MATCH
    assert result.confidence_score == 1.0
    assert len(result.line_results) == 1
    assert result.line_results[0].match_status == MatchStatus.MATCH


def test_price_variance_exceeding_tolerance(sample_vendor, sample_po, sample_grn):
    po, po_items = sample_po
    grns, grn_items = sample_grn
    # 2% tolerance
    matcher = ThreeWayMatcher(tolerance=ToleranceConfig(price_tolerance_pct=0.02))

    # Billed $11.00 per unit instead of $10.00 (10% variance)
    invoice = ExtractedInvoice(
        invoice_number="INV-002",
        vendor_name="Apex Industrial Hardware",
        purchase_order_number="PO-2026-99",
        line_items=[
            ExtractedLineItem(
                line_number=1,
                description="Industrial Grade Steel Bolts M12",
                quantity=100.0,
                unit_price=11.0,
                total_amount=1100.0,
            )
        ],
        subtotal=1100.0,
        tax_amount=0.0,
        total_amount=1100.0,
    )

    result = matcher.reconcile(
        invoice=invoice,
        vendor=sample_vendor,
        po=po,
        po_items=po_items,
        goods_receipts=grns,
        grn_items=grn_items,
    )

    assert result.is_matched is False
    assert result.overall_status == MatchStatus.PRICE_VARIANCE
    assert result.confidence_score < 1.0
    assert MismatchReasonCode.PRICE_VARIANCE in result.line_results[0].mismatch_reasons


def test_quantity_discrepancy_exceeding_po(sample_vendor, sample_po, sample_grn):
    po, po_items = sample_po
    grns, grn_items = sample_grn
    matcher = ThreeWayMatcher()

    # Billed for 120 units, but PO and GRN have 100
    invoice = ExtractedInvoice(
        invoice_number="INV-003",
        vendor_name="Apex Industrial Hardware",
        purchase_order_number="PO-2026-99",
        line_items=[
            ExtractedLineItem(
                line_number=1,
                description="Industrial Grade Steel Bolts M12",
                quantity=120.0,
                unit_price=10.0,
                total_amount=1200.0,
            )
        ],
        subtotal=1200.0,
        tax_amount=0.0,
        total_amount=1200.0,
    )

    result = matcher.reconcile(
        invoice=invoice,
        vendor=sample_vendor,
        po=po,
        po_items=po_items,
        goods_receipts=grns,
        grn_items=grn_items,
    )

    assert result.is_matched is False
    assert result.overall_status == MatchStatus.QUANTITY_DISCREPANCY
    assert MismatchReasonCode.QUANTITY_DISCREPANCY in result.line_results[0].mismatch_reasons


def test_missing_po_returns_unmatched(sample_vendor):
    matcher = ThreeWayMatcher()
    invoice = ExtractedInvoice(
        invoice_number="INV-004",
        vendor_name="Apex Industrial Hardware",
        purchase_order_number="PO-UNKNOWN",
        line_items=[
            ExtractedLineItem(
                line_number=1,
                description="Parts",
                quantity=1.0,
                unit_price=50.0,
                total_amount=50.0,
            )
        ],
        subtotal=50.0,
        tax_amount=0.0,
        total_amount=50.0,
    )

    result = matcher.reconcile(invoice=invoice, vendor=sample_vendor, po=None)
    assert result.is_matched is False
    assert result.overall_status == MatchStatus.UNMATCHED
    assert "not found" in result.anomalies[0]
