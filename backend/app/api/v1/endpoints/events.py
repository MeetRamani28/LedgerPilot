from typing import Optional
from fastapi import APIRouter, Depends, Header, Query, Request
from sse_starlette.sse import EventSourceResponse
from app.core.auth import ClerkUser, get_current_user
from app.services.events.manager import event_broadcaster

router = APIRouter(prefix="/invoices", tags=["Events"])


@router.get("/{invoice_id}/events")
async def stream_invoice_events(
    request: Request,
    invoice_id: str,
    last_event_id: Optional[str] = Header(None, alias="Last-Event-ID"),
    token: Optional[str] = Query(None),
):
    # Support query token for browser EventSource client
    # Or rely on standard Authorization header if present
    # Authenticate user if token provided
    return EventSourceResponse(
        event_broadcaster.subscribe(invoice_id=invoice_id, last_event_id=last_event_id),
        headers={
            "X-Accel-Buffering": "no",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )
