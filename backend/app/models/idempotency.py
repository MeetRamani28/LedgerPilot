from datetime import datetime, timezone
from typing import Optional
from sqlmodel import Field
from app.models.base import TimestampedModel, generate_uuid, get_utc_now


class IdempotencyKey(TimestampedModel, table=True):
    __tablename__ = "idempotency_keys"

    id: str = Field(default_factory=generate_uuid, primary_key=True)
    key: str = Field(unique=True, index=True, nullable=False)
    user_id: str = Field(index=True, nullable=False)
    request_hash: str = Field(index=True, nullable=False)
    status_code: int = Field(default=200)
    response_body: str = Field(nullable=False)  # JSON-encoded response
    expires_at: Optional[datetime] = Field(default=None)
