from typing import Optional
from sqlmodel import Field
from app.models.base import TimestampedModel, generate_uuid


class AuditLog(TimestampedModel, table=True):
    __tablename__ = "audit_logs"

    id: str = Field(default_factory=generate_uuid, primary_key=True, index=True)
    user_id: str = Field(index=True, nullable=False)
    entity_type: str = Field(index=True, nullable=False)  # "INVOICE", "MATCH", "APPROVAL"
    entity_id: str = Field(index=True, nullable=False)
    action: str = Field(index=True, nullable=False)  # "CREATED", "EXTRACTED", "MATCHED", "APPROVED", "REJECTED"
    actor_type: str = Field(default="SYSTEM")  # "SYSTEM" | "USER"
    actor_id: Optional[str] = Field(default=None)
    previous_state: Optional[str] = Field(default=None)
    new_state: Optional[str] = Field(default=None)
    metadata_json: Optional[str] = Field(default=None)
