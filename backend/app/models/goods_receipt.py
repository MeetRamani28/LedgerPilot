from datetime import date
from typing import Optional
from sqlmodel import Field
from app.models.base import TimestampedModel, generate_uuid


class GoodsReceipt(TimestampedModel, table=True):
    __tablename__ = "goods_receipts"

    id: str = Field(default_factory=generate_uuid, primary_key=True, index=True)
    user_id: str = Field(index=True, nullable=False)
    purchase_order_id: str = Field(foreign_key="purchase_orders.id", index=True, nullable=False)
    grn_number: str = Field(index=True, nullable=False)
    receipt_date: date = Field(nullable=False)
    received_by: str = Field(default="Receiving Dept")
    notes: Optional[str] = Field(default=None)


class GoodsReceiptItem(TimestampedModel, table=True):
    __tablename__ = "goods_receipt_items"

    id: str = Field(default_factory=generate_uuid, primary_key=True, index=True)
    goods_receipt_id: str = Field(foreign_key="goods_receipts.id", index=True, nullable=False)
    po_line_item_id: str = Field(foreign_key="po_line_items.id", index=True, nullable=False)
    item_sku: Optional[str] = Field(default=None)
    quantity_received: float = Field(default=0.0)
    condition: str = Field(default="GOOD")
