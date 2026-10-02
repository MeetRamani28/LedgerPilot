import asyncio
import json
from datetime import datetime, timezone
from typing import AsyncGenerator, Optional
from pydantic import BaseModel, Field


class SSEEventEnvelope(BaseModel):
    event_id: str
    type: str = Field(default="STATUS_CHANGE")  # STATUS_CHANGE | PROGRESS | ERROR
    invoice_id: str
    status: str
    progress: int = Field(ge=0, le=100)
    message: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_sse_format(self) -> dict:
        return {
            "id": self.event_id,
            "event": self.type,
            "data": self.model_dump_json(),
        }


class EventBroadcaster:
    def __init__(self):
        # Map: invoice_id -> list[asyncio.Queue]
        self._subscribers: dict[str, list[asyncio.Queue]] = {}
        # Map: invoice_id -> list[SSEEventEnvelope] (ordered history)
        self._history: dict[str, list[SSEEventEnvelope]] = {}
        self._event_counter: int = 0
        self._lock = asyncio.Lock()

    async def publish(
        self,
        invoice_id: str,
        status: str,
        progress: int,
        message: str,
        event_type: str = "STATUS_CHANGE",
    ) -> SSEEventEnvelope:
        async with self._lock:
            self._event_counter += 1
            event_id = f"evt_{self._event_counter:06d}"

            envelope = SSEEventEnvelope(
                event_id=event_id,
                type=event_type,
                invoice_id=invoice_id,
                status=status,
                progress=progress,
                message=message,
            )

            # Store in history buffer (up to 50 events per invoice)
            if invoice_id not in self._history:
                self._history[invoice_id] = []
            self._history[invoice_id].append(envelope)
            if len(self._history[invoice_id]) > 50:
                self._history[invoice_id].pop(0)

            # Broadcast to active queues
            queues = list(self._subscribers.get(invoice_id, []))
            for q in queues:
                await q.put(envelope)

            return envelope

    async def subscribe(
        self,
        invoice_id: str,
        last_event_id: Optional[str] = None,
    ) -> AsyncGenerator[dict, None]:
        q: asyncio.Queue = asyncio.Queue()

        async with self._lock:
            if invoice_id not in self._subscribers:
                self._subscribers[invoice_id] = []
            self._subscribers[invoice_id].append(q)

            # Replay any history if client reconnects with Last-Event-ID or is catching up
            history = self._history.get(invoice_id, [])
            replay_events = []
            if last_event_id:
                seen = False
                for evt in history:
                    if seen:
                        replay_events.append(evt)
                    elif evt.event_id == last_event_id:
                        seen = True
            else:
                # If no last_event_id, send latest event if available so client gets current state
                if history:
                    replay_events = [history[-1]]

        # Yield caught up events
        for evt in replay_events:
            yield evt.to_sse_format()

        # Stream real-time events
        try:
            while True:
                try:
                    # Heartbeat ping every 15s to keep Render / proxy alive
                    envelope: SSEEventEnvelope = await asyncio.wait_for(q.get(), timeout=15.0)
                    yield envelope.to_sse_format()
                except asyncio.TimeoutError:
                    # Emits standard SSE comment heartbeat: ": ping\n\n"
                    yield {"comment": "ping"}
        finally:
            async with self._lock:
                if invoice_id in self._subscribers and q in self._subscribers[invoice_id]:
                    self._subscribers[invoice_id].remove(q)
                    if not self._subscribers[invoice_id]:
                        del self._subscribers[invoice_id]


event_broadcaster = EventBroadcaster()
