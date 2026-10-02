from enum import Enum
from typing import Optional
from sqlmodel import Field
from app.models.base import TimestampedModel, generate_uuid


class MatchStatus(str, Enum):
    MATCH = "MATCH"
    PRICE_VARIANCE = "PRICE_VARIANCE"
    QUANTITY_DISCREPANCY = "QUANTITY_DISCREPANCY"
    UNMATCHED = "UNMATCHED"


class LineItem(TimestampedModel, table=True):
    __tablename__ = "line_items"

    id: str = Field(default_factory=generate_uuid, primary_key=True, index=True)
    invoice_id: str = Field(foreign_key="invoices.id", index=True, nullable=False)
    line_number: int = Field(default=1)
    description: str = Field(nullable=False)
    quantity: float = Field(default=1.0)
    unit_price: float = Field(default=0.0)
    total_amount: float = Field(default=0.0)

    # Reconciliation fields
    po_line_item_id: Optional[str] = Field(default=None, index=True)
    match_status: MatchStatus = Field(default=MatchStatus.UNMATCHED, index=True)
    price_variance: Optional[float] = Field(default=0.0)
    quantity_variance: Optional[float] = Field(default=0.0)
    mismatch_reason: Optional[str] = Field(default=None)
