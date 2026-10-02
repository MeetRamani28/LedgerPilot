from enum import Enum
from datetime import date
from typing import Optional
from sqlmodel import Field
from app.models.base import TimestampedModel, generate_uuid


class InvoiceStatus(str, Enum):
    UPLOADED = "UPLOADED"
    EXTRACTING = "EXTRACTING"
    MATCHING = "MATCHING"
    ANOMALY_CHECK = "ANOMALY_CHECK"
    READY_FOR_REVIEW = "READY_FOR_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    FAILED = "FAILED"


class Invoice(TimestampedModel, table=True):
    __tablename__ = "invoices"

    id: str = Field(default_factory=generate_uuid, primary_key=True, index=True)
    user_id: str = Field(index=True, nullable=False)
    vendor_id: Optional[str] = Field(default=None, foreign_key="vendors.id", index=True)
    invoice_number: str = Field(index=True, nullable=False)
    invoice_date: Optional[date] = Field(default=None)
    due_date: Optional[date] = Field(default=None)
    currency: str = Field(default="USD", max_length=3)
    subtotal: float = Field(default=0.0)
    tax_amount: float = Field(default=0.0)
    total_amount: float = Field(default=0.0, index=True)
    status: InvoiceStatus = Field(default=InvoiceStatus.UPLOADED, index=True)
    file_url: str = Field(nullable=False)
    storage_key: str = Field(nullable=False)
    file_hash: str = Field(index=True, nullable=False)
    confidence_score: Optional[float] = Field(default=None)
    anomaly_flags: Optional[str] = Field(default=None)  # JSON-encoded array of anomaly strings
    rejection_reason: Optional[str] = Field(default=None)
