import asyncio
import io
import json
import logging
import sys
from pathlib import Path

# Ensure backend root is in sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import uuid
from sqlmodel import select
from app.db.session import init_db, async_session_factory
from app.db.seed import seed_database
from app.models.invoice import Invoice
from app.models.line_item import LineItem
from app.services.pipeline import run_reconciliation_pipeline
from app.services.storage.local_storage import LocalStorageService
from tests.fixtures.sample_invoices import (
    generate_happy_path_invoice,
    generate_price_drift_invoice,
    generate_quantity_mismatch_invoice,
    generate_duplicate_invoice,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("run_local_demo")


async def run_scenario(name: str, pdf_bytes: bytes, user_id: str) -> dict:
    storage = LocalStorageService()
    file_url, storage_key = await storage.upload(pdf_bytes, f"{name}.pdf")

    async with async_session_factory() as session:
        inv = Invoice(
            user_id=user_id,
            invoice_number=f"PENDING-{name}",
            file_url=file_url,
            storage_key=storage_key,
            file_hash=uuid.uuid4().hex,
        )
        session.add(inv)
        await session.commit()
        await session.refresh(inv)
        invoice_id = inv.id

    # Execute pipeline
    await run_reconciliation_pipeline(invoice_id, pdf_bytes, user_id)

    async with async_session_factory() as session:
        res = await session.get(Invoice, invoice_id)
        line_stmt = select(LineItem).where(LineItem.invoice_id == invoice_id)
        line_res = await session.exec(line_stmt)
        lines = list(line_res.all())

        return {
            "name": name,
            "invoice_number": res.invoice_number,
            "status": res.status.value,
            "confidence": res.confidence_score,
            "anomalies": json.loads(res.anomaly_flags) if res.anomaly_flags else [],
            "lines": [
                {
                    "desc": l.description,
                    "qty": l.quantity,
                    "unit_price": l.unit_price,
                    "status": l.match_status.value,
                    "mismatch_reason": l.mismatch_reason,
                }
                for l in lines
            ],
        }


async def main():
    print("=" * 70)
    print("      LEDGERPILOT: LOCAL PIPELINE RECONCILIATION DRY RUN")
    print("=" * 70)

    demo_user = f"demo_runner_{uuid.uuid4().hex[:8]}"
    await init_db()

    async with async_session_factory() as session:
        await seed_database(session, user_id=demo_user)

    scenarios = [
        ("1. Happy Path Match (100% 3-Way Match)", generate_happy_path_invoice),
        ("2. Price Drift (>5% Variance Flagged)", generate_price_drift_invoice),
        ("3. Quantity Mismatch (Billed 10 vs PO 5)", generate_quantity_mismatch_invoice),
        ("4. Duplicate Invoice Anomaly", generate_duplicate_invoice),
    ]

    for label, generator in scenarios:
        print(f"\n---> Running Scenario: {label}")
        pdf_bytes, meta = generator()
        result = await run_scenario(label, pdf_bytes, user_id=demo_user)

        print(f"     Invoice Number : {result['invoice_number']}")
        print(f"     Status         : {result['status']}")
        print(f"     Confidence     : {result['confidence']}")
        print(f"     Anomalies      : {result['anomalies']}")
        for l in result["lines"]:
            print(f"     Line Item      : {l['desc'][:30]} | Match: {l['status']} | Reason: {l['mismatch_reason']}")

    print("\n" + "=" * 70)
    print("      DRY RUN COMPLETED SUCCESSFULLY FOR ALL 4 SCENARIOS")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
