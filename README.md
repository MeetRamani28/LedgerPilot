# LedgerPilot 🚀
> **AI-Powered Autonomous Accounts-Payable & Invoice Reconciliation Pipeline**

LedgerPilot is an enterprise-grade accounts-payable and invoice reconciliation engine built with FastAPI, React, Groq LPU Vision, and Clerk multi-device authentication.

---

## 🏛 Architecture Overview

```
+----------------------------------------------------------------------------------------------------+
|                                         LEDGERPILOT WORKFLOW                                       |
+----------------------------------------------------------------------------------------------------+

  [AP Clerk / Client]
         |
         |  1. POST /api/v1/invoices/upload (PDF + Idempotency-Key)
         v
+------------------------ Backend (FastAPI on Render) ------------------------------------------------+
|                                                                                                    |
|  [Idempotency Check] ---> (Duplicate Hash?) ---> Return existing invoice record                   |
|         | (New)                                                                                    |
|         v                                                                                          |
|  [Storage / DB] --------> Save PDF & create Invoice row (Status: UPLOADED)                         |
|         |                                                                                          |
|         +-------------------+                                                                      |
|                             |                                                                      |
|  [Background Task / Worker] | 2. SSE Stream: GET /api/v1/invoices/{id}/events                      |
|         |                   +---------------------------------------------> [Client EventSource]   |
|         |                                                                            ^             |
|         |-- Emit: EXTRACTING (progress: 20%) ----------------------------------------|             |
|         v                                                                            |             |
|  [Groq LPU Vision Engine]                                                            |             |
|         |-- Structured Pydantic v2 JSON Schema Extraction                            |             |
|         |-- Retry with Exponential Backoff                                           |             |
|         v                                                                            |             |
|  [Structured Invoice Data JSON]                                                      |             |
|         |                                                                            |             |
|         |-- Emit: MATCHING (progress: 50%) ------------------------------------------|             |
|         v                                                                            |             |
|  [3-Way Match Engine] <===> [Vendor / PO / GoodsReceipts DB + Vector Store]          |             |
|         |-- 1. Match Invoice Vendor -> DB Vendor (Chroma / Pinecone hybrid lookup)   |             |
|         |-- 2. Line Item Matching: Invoice Lines vs PO Lines vs Goods Receipts       |             |
|         |-- 3. Tolerance Checks: Qty <= tol%, Price <= tol%, Totals math             |             |
|         v                                                                            |             |
|  [Anomaly Engine]                                                                    |             |
|         |-- Emit: ANOMALY_CHECK (progress: 80%) -------------------------------------|             |
|         |-- Verify duplicate invoice #, tax anomalies, ghost vendors                 |             |
|         v                                                                            |             |
|  [State Finalization]                                                                |             |
|         |-- Calculate Match Confidence Score                                         |             |
|         |-- Status -> READY_FOR_REVIEW                                               |             |
|         |-- Emit: READY_FOR_REVIEW (progress: 100%) ---------------------------------|             |
|                                                                                                    |
+----------------------------------------------------------------------------------------------------+
```

---

## 🛠 Tech Stack

- **Backend:** Python 3.12, FastAPI, `uv` package manager, SQLModel / SQLAlchemy 2.0 (SQLite / Supabase Postgres), Groq Vision LPU (`llama-3.2-11b-vision-preview`), ChromaDB / Pinecone vector store, Clerk JWT session auth.
- **Frontend:** React 19, TypeScript, Vite, Tailwind CSS v4 (`@tailwindcss/vite`), TanStack Query, Redux Toolkit, Clerk Multi-Device Auth.
- **Real-Time Updates:** Server-Sent Events (SSE) with `Last-Event-ID` resume and heartbeat keep-alives.

---

## 🚀 Quickstart

### Backend
```powershell
cd backend
uv run uvicorn app.main:app --reload
```
To run tests:
```powershell
cd backend
uv run pytest
```

### Frontend
```powershell
cd frontend
npm run dev
```
To build:
```powershell
cd frontend
npm run build
```
