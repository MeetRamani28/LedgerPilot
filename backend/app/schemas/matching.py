from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field
from app.models.line_item import MatchStatus


class MismatchReasonCode(str, Enum):
    PRICE_VARIANCE = "PRICE_VARIANCE"
    QUANTITY_DISCREPANCY = "QUANTITY_DISCREPANCY"
    MISSING_PO = "MISSING_PO"
    MISSING_GOODS_RECEIPT = "MISSING_GOODS_RECEIPT"
    UNKNOWN_VENDOR = "UNKNOWN_VENDOR"
    LINE_ITEM_UNMATCHED = "LINE_ITEM_UNMATCHED"
    TOTAL_AMOUNT_MISMATCH = "TOTAL_AMOUNT_MISMATCH"
    DUPLICATE_INVOICE = "DUPLICATE_INVOICE"
    TAX_RATE_ANOMALY = "TAX_RATE_ANOMALY"


class LineItemMatchResult(BaseModel):
    line_number: int
    invoice_description: str
    invoice_qty: float
    invoice_unit_price: float
    invoice_total: float

    po_line_id: Optional[str] = None
    po_sku: Optional[str] = None
    po_qty: Optional[float] = None
    po_unit_price: Optional[float] = None
    received_qty: Optional[float] = None

    match_status: MatchStatus = MatchStatus.UNMATCHED
    price_variance_pct: float = 0.0
    quantity_variance_pct: float = 0.0
    mismatch_reasons: list[MismatchReasonCode] = Field(default_factory=list)


class MatchResult(BaseModel):
    invoice_id: Optional[str] = None
    vendor_id: Optional[str] = None
    po_id: Optional[str] = None

    overall_status: MatchStatus = MatchStatus.UNMATCHED
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0)
    is_matched: bool = False
    line_results: list[LineItemMatchResult] = Field(default_factory=list)
    anomalies: list[str] = Field(default_factory=list)
    total_variance: float = 0.0
    summary: str = ""
