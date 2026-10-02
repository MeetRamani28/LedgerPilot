from enum import Enum
from datetime import date
from typing import Optional
from sqlmodel import Field
from app.models.base import TimestampedModel, generate_uuid


class POStatus(str, Enum):
    OPEN = "OPEN"
    PARTIALLY_RECEIVED = "PARTIALLY_RECEIVED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class PurchaseOrder(TimestampedModel, table=True):
    __tablename__ = "purchase_orders"

    id: str = Field(default_factory=generate_uuid, primary_key=True, index=True)
    user_id: str = Field(index=True, nullable=False)
    vendor_id: str = Field(foreign_key="vendors.id", index=True, nullable=False)
    po_number: str = Field(index=True, nullable=False)
    order_date: date = Field(nullable=False)
    total_amount: float = Field(default=0.0)
    status: POStatus = Field(default=POStatus.OPEN, index=True)


class POLineItem(TimestampedModel, table=True):
    __tablename__ = "po_line_items"

    id: str = Field(default_factory=generate_uuid, primary_key=True, index=True)
    purchase_order_id: str = Field(foreign_key="purchase_orders.id", index=True, nullable=False)
    line_number: int = Field(default=1)
    item_sku: Optional[str] = Field(default=None, index=True)
    description: str = Field(nullable=False)
    quantity: float = Field(default=1.0)
    unit_price: float = Field(default=0.0)
    total_amount: float = Field(default=0.0)
    quantity_received: float = Field(default=0.0)
