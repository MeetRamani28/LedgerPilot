import pytest
from app.services.events.manager import EventBroadcaster


@pytest.mark.anyio
async def test_event_broadcaster_publish_and_history():
    broadcaster = EventBroadcaster()
    invoice_id = "inv_sse_test_1"

    # 1. Publish 3 events
    e1 = await broadcaster.publish(
        invoice_id=invoice_id,
        status="EXTRACTING",
        progress=20,
        message="Extracting data",
    )
    assert e1.event_id == "evt_000001"
    assert e1.progress == 20

    e2 = await broadcaster.publish(
        invoice_id=invoice_id,
        status="MATCHING",
        progress=50,
        message="Matching PO",
    )
    assert e2.event_id == "evt_000002"

    e3 = await broadcaster.publish(
        invoice_id=invoice_id,
        status="READY_FOR_REVIEW",
        progress=100,
        message="Review ready",
    )
    assert e3.event_id == "evt_000003"

    # 2. Subscribe with Last-Event-ID to test replay
    subscription = broadcaster.subscribe(invoice_id=invoice_id, last_event_id="evt_000001")
    replayed = []
    # Read the two replayed items (evt_000002 and evt_000003)
    async for item in subscription:
        replayed.append(item)
        if len(replayed) == 2:
            break

    assert len(replayed) == 2
    assert replayed[0]["id"] == "evt_000002"
    assert replayed[1]["id"] == "evt_000003"
