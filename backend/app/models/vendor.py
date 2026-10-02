from typing import Optional
from sqlmodel import Field, SQLModel
from app.models.base import TimestampedModel, generate_uuid


class Vendor(TimestampedModel, table=True):
    __tablename__ = "vendors"

    id: str = Field(default_factory=generate_uuid, primary_key=True, index=True)
    user_id: str = Field(index=True, nullable=False)
    name: str = Field(index=True, nullable=False)
    normalized_name: str = Field(index=True, nullable=False)
    tax_id: Optional[str] = Field(default=None, index=True)
    address: Optional[str] = Field(default=None)
    contact_email: Optional[str] = Field(default=None)
    payment_terms: str = Field(default="Net 30")
    is_active: bool = Field(default=True)
