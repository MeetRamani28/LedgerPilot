# LedgerPilot: Autonomous Accounts-Payable & Invoice Reconciliation Pipeline
## Master 20-Step Production Execution Plan

> **Architectural Standard:** Enterprise-grade production engineering. Test-Driven Development (TDD) across all phases. Zero hardcoded secrets. Strict separation of concerns between `frontend/` and `backend/`.

---

### Architectural Additions & Updates (Approved Phase 1 Extensions)
1. **Vision Extraction Provider:** Abstracted `ExtractionService` with primary implementation on **Groq Vision API** (`llama-3.2-11b-vision-preview` / `llama-3.2-90b-vision-preview` via `groq` SDK) with fallback to **Cohere** (`cohere` SDK) and a deterministic `MockExtractor` for pytest. Configured via `EXTRACTION_PROVIDER=groq|cohere|mock`.
2. **Storage Subsystem:** Environment-controlled storage via `StorageService`:
   - `STORAGE_PROVIDER=local`: Saves files directly to `backend/uploads/` with UUID-namespaced paths for local dev.
   - `STORAGE_PROVIDER=supabase`: Streams binaries directly to Supabase Storage private buckets via `supabase-py` for production.
3. **Authentication & Multi-Device Session Persistence:**
   - **Clerk Authentication** integrated via `@clerk/clerk-react` on frontend and Clerk JWKS token verification middleware/dependency on FastAPI backend.
   - **Multi-Device Parity:** Clerk native session handling maintains $\ge 5$ concurrent persistent sessions across mobile, desktop, and tablet environments without cross-device session invalidation.
   - **Data Isolation:** Backend decodes and cryptographically verifies the bearer JWT against Clerk JWKS, extracting the invariant `userId` (`sub` claim) to ensure strictly scoped data ownership across all transactions and SSE event streams.

---

## PART 1: LOCAL DEVELOPMENT (Steps 1–10)

### Step 1: Project Initialization, Repository Hygiene & Tooling Setup
- **(1) Objective:** Initialize the monorepo root with strict boundary separation (`frontend/`, `backend/`, `docs/`), initialize git on `main`, bind remote `origin` to `https://github.com/MeetRamani28/LedgerPilot.git`, configure top-level `.gitignore`, bootstrap Python backend using `uv`, and scaffold React + Vite + Tailwind frontend.
- **(2) Files to create/modify:**
  - `.gitignore` (Root: Node, Python, Vite, OS, `.env`, uploads, chroma caches)
  - `backend/pyproject.toml` (Initialized via `uv init`)
  - `backend/.env.example`
  - `frontend/package.json` (Initialized via Vite)
  - `frontend/vite.config.ts`
  - `frontend/tsconfig.json`
  - `frontend/tailwind.config.js`, `frontend/postcss.config.js`
  - `frontend/.env.example`
  - `README.md`
- **(3) Commands:**
  ```powershell
  # Git init
  git init -b main
  git remote add origin https://github.com/MeetRamani28/LedgerPilot.git

  # Backend init with uv
  uv init backend --app --python 3.12
  cd backend
  uv add fastapi "uvicorn[standard]" pydantic pydantic-settings python-dotenv pytest httpx
  cd ..

  # Frontend init with Vite
  npm create vite@latest frontend -- --template react-ts
  cd frontend
  npm install
  npm install -D tailwindcss postcss autoprefixer
  npx tailwindcss init -p
  cd ..
  ```
- **(4) Verification criteria:**
  - `git status` reflects clean tree on branch `main` with remote configured (`git remote -v`).
  - Backend tests run cleanly: `cd backend; uv run pytest; cd ..`
  - Frontend builds cleanly: `cd frontend; npm run build; cd ..`
- **(5) Conventional Commit message:**
  `chore(init): scaffold monorepo with uv backend, vite frontend, and repo hygiene`

---

### Step 2: Database Layer, SQLModel Schema & Vector Store Abstraction
- **(1) Objective:** Establish relational schema and vector-store abstractions. Define core relational tables (`Vendors`, `Invoices`, `LineItems`, `PurchaseOrders`, `GoodsReceipts`, `AuditLogs`, `IdempotencyKeys`) using SQLAlchemy 2.0 / SQLModel with a Repository pattern (`DB_PROVIDER=sqlite|postgres`). Build a unified vector interface `IVectorStore` with local `ChromaVectorStore` implementation (`VECTOR_PROVIDER=chroma|pinecone`). Include user ownership on all records via `user_id`.
- **(2) Files to create/modify:**
  - `backend/app/db/session.py` (Engine factory switching between SQLite and Postgres)
  - `backend/app/models/base.py`
  - `backend/app/models/vendor.py`
  - `backend/app/models/invoice.py`
  - `backend/app/models/line_item.py`
  - `backend/app/models/purchase_order.py`
  - `backend/app/models/goods_receipt.py`
  - `backend/app/models/audit_log.py`
  - `backend/app/models/idempotency.py`
  - `backend/app/services/vector/base.py` (`IVectorStore` interface)
  - `backend/app/services/vector/chroma_store.py` (`ChromaVectorStore`)
  - `backend/app/db/repository.py` (Generic DB repository)
  - `backend/tests/test_db_models.py`
  - `backend/tests/test_vector_store.py`
- **(3) Commands:**
  ```powershell
  cd backend
  uv add sqlmodel sqlalchemy aiosqlite chromadb
  uv run pytest tests/test_db_models.py tests/test_vector_store.py
  cd ..
  ```
- **(4) Verification criteria:**
  - SQLite creates all tables without schema warnings.
  - Foreign key cascades and index constraints validate in unit tests.
  - Chroma vector store passes document insertion, similarity query, and collection deletion tests.
- **(5) Conventional Commit message:**
  `feat(db): implement relational models, repository pattern, and chroma vector abstraction`

---

### Step 3: Pydantic Invoice Schemas & Vision Extraction Engine (Groq / Cohere / Mock)
- **(1) Objective:** Build strict Pydantic v2 validation models for invoices and line items enforcing mathematical invariants ($\sum(\text{qty} \times \text{unit\_price}) + \text{tax} = \text{total} \pm \$0.02$). Create an `ExtractionService` supporting `GroqVisionExtractor` (Llama 3.2 Vision via Groq), `CohereExtractor`, and a deterministic `MockExtractor` for pytest. Implement PDF page rasterization (`pypdfium2`) to feed image base64 payloads to vision models, with exponential backoff retry via `tenacity`.
- **(2) Files to create/modify:**
  - `backend/app/schemas/invoice_extraction.py` (Pydantic v2 models with arithmetic validators)
  - `backend/app/services/extraction/base.py` (`IExtractionService`)
  - `backend/app/services/extraction/mock_extractor.py` (`MockExtractor` for unit tests)
  - `backend/app/services/extraction/groq_extractor.py` (`GroqVisionExtractor`)
  - `backend/app/services/extraction/cohere_extractor.py` (`CohereExtractor`)
  - `backend/app/services/extraction/pdf_utils.py` (PDF to image conversion)
  - `backend/app/services/extraction/factory.py` (Provider selector)
  - `backend/tests/test_invoice_schemas.py`
  - `backend/tests/test_mock_extractor.py`
- **(3) Commands:**
  ```powershell
  cd backend
  uv add groq cohere tenacity pypdfium2 pillow
  uv run pytest tests/test_invoice_schemas.py tests/test_mock_extractor.py
  cd ..
  ```
- **(4) Verification criteria:**
  - Pydantic models reject invalid tax/total calculations and missing required fields.
  - `MockExtractor` extracts valid structured JSON matching schemas without calling external APIs.
  - PDF utility converts sample PDF byte streams to clean PNG/JPEG buffers.
- **(5) Conventional Commit message:**
  `feat(extraction): implement pydantic schemas and pluggable vision extraction service`

---

### Step 4: Three-Way Matching & Anomaly Detection Engine
- **(1) Objective:** Implement business logic for 3-way matching between Invoice, Purchase Order, and Goods Receipt. Support configurable tolerance thresholds (quantity delta %, unit price variance %, total threshold) and distinct mismatch reason codes (`PRICE_VARIANCE`, `QUANTITY_DISCREPANCY`, `MISSING_PO`, `MISSING_GOODS_RECEIPT`, `UNKNOWN_VENDOR`, `LINE_ITEM_UNMATCHED`). Implement anomaly checks for duplicate invoices, suspicious tax rates, and unverified vendors.
- **(2) Files to create/modify:**
  - `backend/app/schemas/matching.py` (Match result schemas, reason codes, confidence scoring)
  - `backend/app/services/matching/tolerance_config.py`
  - `backend/app/services/matching/matcher.py` (Three-way match logic)
  - `backend/app/services/matching/anomaly_detector.py` (Anomaly detection rules)
  - `backend/tests/test_matching_engine.py`
  - `backend/tests/test_anomaly_detector.py`
- **(3) Commands:**
  ```powershell
  cd backend
  uv run pytest tests/test_matching_engine.py tests/test_anomaly_detector.py
  cd ..
  ```
- **(4) Verification criteria:**
  - Exact match yields `READY_FOR_REVIEW` with 100% confidence.
  - Unit price discrepancies exceeding tolerance trigger `PRICE_VARIANCE` reason code.
  - Quantities exceeding PO without matching Goods Receipt trigger `QUANTITY_DISCREPANCY`.
  - Duplicate invoice checks flag previously recorded numbers for the same vendor.
- **(5) Conventional Commit message:**
  `feat(matching): implement three-way reconciliation engine and anomaly detection`

---

### Step 5: Clerk Auth Verification, Storage Service & Core REST API + SSE
- **(1) Objective:** Build backend Clerk authentication dependency (verifying session tokens via Clerk JWKS, decoding `user_id`), local `StorageService` (`backend/uploads/`), REST endpoints (`/api/v1/invoices/upload`, `GET /invoices`, `GET /invoices/{id}`, `POST /invoices/{id}/approve`, `POST /invoices/{id}/reject`, `/audit-logs`), and Server-Sent Events stream (`GET /api/v1/invoices/{id}/events`) using `sse-starlette` with heartbeat pings and `Last-Event-ID` resume support.
- **(2) Files to create/modify:**
  - `backend/app/core/config.py` (Settings with Pydantic `BaseSettings`)
  - `backend/app/core/auth.py` (Clerk JWKS token verification dependency)
  - `backend/app/services/storage/base.py` (`IStorageService`)
  - `backend/app/services/storage/local_storage.py` (`LocalStorageService`)
  - `backend/app/services/events/manager.py` (In-memory pub/sub event broadcaster for SSE)
  - `backend/app/api/v1/endpoints/invoices.py`
  - `backend/app/api/v1/endpoints/events.py`
  - `backend/app/api/v1/endpoints/audit_logs.py`
  - `backend/app/main.py` (FastAPI app factory, CORS, exception handlers)
  - `backend/tests/test_invoices_api.py`
  - `backend/tests/test_sse_events.py`
- **(3) Commands:**
  ```powershell
  cd backend
  uv add sse-starlette PyJWT cryptography python-multipart
  uv run pytest tests/test_invoices_api.py tests/test_sse_events.py
  cd ..
  ```
- **(4) Verification criteria:**
  - Unauthenticated requests return `401 Unauthorized`.
  - Authenticated multipart upload stores file locally, creates database record, and queues pipeline task.
  - SSE endpoint streams structured event envelopes with headers `X-Accel-Buffering: no` and periodic comment heartbeats.
- **(5) Conventional Commit message:**
  `feat(api): add clerk auth dependency, invoice endpoints, and sse event stream`

---

### Step 6: Frontend Base: Clerk Provider, TanStack Query, Redux Toolkit & UI Shell
- **(1) Objective:** Set up frontend architecture with `@clerk/clerk-react` for multi-device persistent session management, TanStack Query for server state caching/invalidation, Redux Toolkit for local UI state (sidebar collapse, document zoom, active line item selection, modal states), Lucide icons, Sonner toast notifications, and standard application shell layout (Navbar with Clerk `<UserButton />`, Sidebar, Breadcrumbs).
- **(2) Files to create/modify:**
  - `frontend/src/app/store.ts` (Redux Toolkit store)
  - `frontend/src/features/ui/uiSlice.ts` (Viewer zoom, selected item, theme)
  - `frontend/src/lib/api-client.ts` (Axios / Fetch with Clerk auth interceptor)
  - `frontend/src/lib/query-client.ts` (TanStack Query client configuration)
  - `frontend/src/components/layout/AppShell.tsx`
  - `frontend/src/components/layout/Navbar.tsx`
  - `frontend/src/components/layout/Sidebar.tsx`
  - `frontend/src/App.tsx`
  - `frontend/src/main.tsx`
- **(3) Commands:**
  ```powershell
  cd frontend
  npm install @clerk/clerk-react @tanstack/react-query @reduxjs/toolkit react-redux lucide-react sonner clsx tailwind-merge
  npm run build
  cd ..
  ```
- **(4) Verification criteria:**
  - Frontend compiles with zero TypeScript errors.
  - App displays clean layout with navigation and authenticated user session handling.
  - Multi-device sessions persist upon refresh without triggering sign-out.
- **(5) Conventional Commit message:**
  `feat(frontend): initialize clerk auth, redux toolkit, tanstack query, and app shell`

---

### Step 7: PDF Upload Zone & Split-Screen Document Viewer
- **(1) Objective:** Build drag-and-drop PDF upload component with client-side file validation (size limits, MIME checks) and a responsive split-screen document viewer using `react-pdf` (or PDF.js canvas wrapper) with pagination, zoom controls, pan, and visual bounding-box overlay support.
- **(2) Files to create/modify:**
  - `frontend/src/components/upload/FileUploadDropzone.tsx`
  - `frontend/src/components/viewer/PdfViewer.tsx`
  - `frontend/src/components/viewer/ViewerControls.tsx`
  - `frontend/src/features/invoices/useUploadInvoice.ts`
  - `frontend/src/pages/InvoiceDetailPage.tsx`
- **(3) Commands:**
  ```powershell
  cd frontend
  npm install react-pdf pdfjs-dist
  npm run build
  cd ..
  ```
- **(4) Verification criteria:**
  - Dropping a valid PDF initiates multipart upload with progress indicator.
  - Split-screen viewer renders PDF pages cleanly on desktop and tablet screens.
  - Zoom in/out and page navigation work without canvas distortion.
- **(5) Conventional Commit message:**
  `feat(frontend): build drag-and-drop pdf uploader and split-screen document viewer`

---

### Step 8: Extracted Data Review, Line-Item Table & Match Diff Badges
- **(1) Objective:** Build the right-hand review panel: Vendor header cards, editable line-item table (quantity, unit price, description, total), tolerance variance badges (`MATCH`, `VARIANCE`, `MISMATCH`), PO reference link, and an action bar (Approve, Reject with Reason modal, Re-run Match).
- **(2) Files to create/modify:**
  - `frontend/src/components/review/InvoiceHeaderCard.tsx`
  - `frontend/src/components/review/LineItemTable.tsx`
  - `frontend/src/components/review/MatchStatusBadge.tsx`
  - `frontend/src/components/review/ToleranceVarianceCard.tsx`
  - `frontend/src/components/review/ApprovalActionBar.tsx`
  - `frontend/src/features/invoices/useInvoiceActions.ts`
- **(3) Commands:**
  ```powershell
  cd frontend
  npm run build
  cd ..
  ```
- **(4) Verification criteria:**
  - Line items render with color-coded variance tags (green within tolerance, amber on minor drift, red on mismatch).
  - Editing line item fields updates calculated subtotals and re-evaluates variances dynamically.
  - Approval and rejection mutations fire correct REST endpoints and display Sonner toasts.
- **(5) Conventional Commit message:**
  `feat(frontend): implement editable line-item review table and match diff badges`

---

### Step 9: Real-Time SSE Stream Integration & Reactive State Invalidation
- **(1) Objective:** Implement client-side SSE subscriber using `@microsoft/fetch-event-source` passing Clerk bearer tokens and `Last-Event-ID`. Wire SSE events directly to TanStack Query cache invalidations and Redux status banners, animating pipeline transitions (`UPLOADED -> EXTRACTING -> MATCHING -> ANOMALY_CHECK -> READY_FOR_REVIEW`) in real time.
- **(2) Files to create/modify:**
  - `frontend/src/lib/sse-client.ts` (Fetch-based SSE client with auth headers and backoff)
  - `frontend/src/hooks/useInvoiceStream.ts` (React hook binding stream to cache updates)
  - `frontend/src/components/pipeline/PipelineProgressBar.tsx`
  - `frontend/src/pages/InvoiceDetailPage.tsx`
- **(3) Commands:**
  ```powershell
  cd frontend
  npm install @microsoft/fetch-event-source
  npm run build
  cd ..
  ```
- **(4) Verification criteria:**
  - Triggering an extraction updates progress bars reactively without manual page refreshes.
  - Network disconnection automatically triggers reconnect with `Last-Event-ID`.
  - When status reaches `READY_FOR_REVIEW`, TanStack Query invalidates and fetches complete review payload.
- **(5) Conventional Commit message:**
  `feat(frontend): integrate authenticated sse stream with reactive cache invalidation`

---

### Step 10: Local End-to-End Integration Suite & Fixture Dry Run
- **(1) Objective:** Build an automated end-to-end integration test harness and seed script with synthetic Purchase Orders, Goods Receipts, Vendors, and test invoice PDFs covering 4 critical edge cases:
  1. *Happy Path:* 100% 3-way match within tolerance.
  2. *Price Drift:* Unit price exceeds configured tolerance ($>5\%$).
  3. *Quantity Mismatch / Missing Receipt:* Billed for 10 units, PO and Goods Receipt show 5.
  4. *Anomaly / Duplicate:* Duplicate invoice number from same vendor.
- **(2) Files to create/modify:**
  - `backend/app/db/seed.py` (Synthetic data generator for POs, GRNs, Vendors)
  - `backend/tests/fixtures/sample_invoices.py` (PDF test generators)
  - `backend/tests/test_e2e_reconciliation.py` (Full pipeline integration test)
  - `backend/scripts/run_local_demo.py`
- **(3) Commands:**
  ```powershell
  cd backend
  uv run python -m app.db.seed
  uv run pytest tests/test_e2e_reconciliation.py -v
  cd ..
  ```
- **(4) Verification criteria:**
  - Seed script successfully populates SQLite database.
  - All 4 test cases evaluate to expected statuses (`READY_FOR_REVIEW`, `FLAGGED_PRICE_VARIANCE`, `FLAGGED_QTY_MISMATCH`, `DUPLICATE_ANOMALY`).
  - Pipeline logs show clean state progressions with zero unhandled exceptions.
- **(5) Conventional Commit message:**
  `test(e2e): add end-to-end pipeline reconciliation suite with edge-case fixtures`

---

## PART 2: PRODUCTION HARDENING (Steps 11–15)

### Step 11: SQLite $\to$ Supabase PostgreSQL Migration via Alembic
- **(1) Objective:** Configure Alembic migrations and verify seamless runtime switching via `DB_PROVIDER=postgres`. Verify pooled asynchronous PostgreSQL connection handling via `asyncpg`, schema generation, migration rollback capability, and Supabase database connection string compatibility.
- **(2) Files to create/modify:**
  - `backend/alembic.ini`
  - `backend/alembic/env.py`
  - `backend/alembic/versions/` (Initial migration script)
  - `backend/app/db/session.py` (Configured for async SQLite vs async Supabase Postgres)
  - `backend/tests/test_postgres_compatibility.py`
- **(3) Commands:**
  ```powershell
  cd backend
  uv add alembic asyncpg psycopg2-binary
  uv run alembic revision --autogenerate -m "initial_schema"
  uv run pytest tests/test_postgres_compatibility.py
  cd ..
  ```
- **(4) Verification criteria:**
  - Alembic generates clean, non-conflicting migration script.
  - Session engine correctly selects SQLite dialect when `DB_PROVIDER=sqlite` and asyncpg when `DB_PROVIDER=postgres`.
  - Migrations apply and roll back cleanly without index collisions.
- **(5) Conventional Commit message:**
  `feat(db): add alembic migrations and asyncpg postgres driver for supabase`

---

### Step 12: Chroma $\to$ Pinecone Vector Provider & Hybrid Vendor Matching
- **(1) Objective:** Implement `PineconeVectorStore` behind `IVectorStore`. Enable dynamic provider selection via `VECTOR_PROVIDER=pinecone|chroma`. Implement hybrid vendor matching algorithm: cosine similarity over vendor embeddings combined with Levenshtein fuzzy string distance and Tax ID exact matching to prevent false-positive vendor resolution.
- **(2) Files to create/modify:**
  - `backend/app/services/vector/pinecone_store.py` (`PineconeVectorStore`)
  - `backend/app/services/vector/factory.py` (Vector store provider factory)
  - `backend/app/services/matching/vendor_matcher.py` (Hybrid embedding + fuzzy algorithm)
  - `backend/tests/test_vendor_matcher.py`
- **(3) Commands:**
  ```powershell
  cd backend
  uv add pinecone-client thefuzz python-Levenshtein
  uv run pytest tests/test_vendor_matcher.py
  cd ..
  ```
- **(4) Verification criteria:**
  - Switching `VECTOR_PROVIDER=pinecone` instantiates Pinecone client using index specified in `.env`.
  - Vendor matcher resolves "Acme Corp Ltd." to "ACME CORPORATION" with high confidence.
  - Unregistered vendor names with low similarity correctly yield `UNKNOWN_VENDOR` status.
- **(5) Conventional Commit message:**
  `feat(vector): implement pinecone adapter and hybrid vendor resolution algorithm`

---

### Step 13: Supabase Storage Integration, Idempotency & Auto-Approve Routing
- **(1) Objective:** Implement `SupabaseStorageService` behind `IStorageService` (`STORAGE_PROVIDER=supabase|local`). Enforce strict idempotency locks using compound hashes `SHA256(PDF_BYTES) + (vendor_id, invoice_number, total)` recorded in `IdempotencyKeys`. Implement confidence-score routing: invoices matching 100% with high confidence and zero anomalies are marked `AUTO_APPROVED`, while drifted invoices route to `READY_FOR_REVIEW`.
- **(2) Files to create/modify:**
  - `backend/app/services/storage/supabase_storage.py` (`SupabaseStorageService`)
  - `backend/app/services/storage/factory.py`
  - `backend/app/services/idempotency/guard.py` (Idempotency middleware/decorator)
  - `backend/app/services/matching/routing.py` (Confidence routing engine)
  - `backend/tests/test_idempotency.py`
  - `backend/tests/test_storage_service.py`
- **(3) Commands:**
  ```powershell
  cd backend
  uv add supabase
  uv run pytest tests/test_idempotency.py tests/test_storage_service.py
  cd ..
  ```
- **(4) Verification criteria:**
  - Re-uploading the exact same PDF returns cached invoice payload with `200 OK` (no re-extraction).
  - Storage provider switches smoothly between local disk and Supabase Storage bucket.
  - Flawless invoices successfully auto-route to `AUTO_APPROVED` when auto-approve policy is enabled.
- **(5) Conventional Commit message:**
  `feat(storage): add supabase bucket adapter, idempotency guards, and auto-routing`

---

### Step 14: Environment Profiles & Comprehensive Security Hardening
- **(1) Objective:** Create battle-tested environment profiles (`.env.example`, `.env.production`), implement strict CORS origins, rate limiting (via `slowapi`), file upload size/type limits (maximum 15MB, PDF MIME only), filename sanitization, security response headers (`Content-Security-Policy`, `X-Content-Type-Options: nosniff`), and Clerk session multi-device verification audit.
- **(2) Files to create/modify:**
  - `backend/.env.example`, `backend/.env.production`
  - `frontend/.env.example`, `frontend/.env.production`
  - `backend/app/core/security.py` (Filename sanitization, magic byte MIME validation)
  - `backend/app/core/rate_limit.py` (SlowAPI rate limiter setup)
  - `backend/app/main.py` (Security headers, CORS middleware)
  - `backend/tests/test_security_audit.py`
- **(3) Commands:**
  ```powershell
  cd backend
  uv add slowapi python-magic-bin
  uv run pytest tests/test_security_audit.py
  cd ..
  ```
- **(4) Verification criteria:**
  - Non-PDF files (e.g. `.exe` disguised as `.pdf`) are rejected by magic byte inspection.
  - Requests exceeding rate limits receive `429 Too Many Requests`.
  - Sensitive keys (`GROQ_API_KEY`, `CLERK_SECRET_KEY`) are verified absent from git history.
- **(5) Conventional Commit message:**
  `security(core): enforce upload validation, rate limiting, and security headers`

---

### Step 15: Production Build Verification & Multi-Worker Server Profile
- **(1) Objective:** Validate optimized production builds. Verify frontend compiles into static bundle without warnings, analyze bundle size, and verify backend executes under Gunicorn + Uvicorn worker model (`uv run gunicorn -w 2 -k uvicorn.workers.UvicornWorker`).
- **(2) Files to create/modify:**
  - `backend/gunicorn_conf.py` (Worker config, timeout, keepalive tuning for SSE)
  - `backend/tests/test_healthz.py`
  - `frontend/vite.config.ts` (Rollup manual chunks split: vendor, pdf, clerk)
- **(3) Commands:**
  ```powershell
  cd frontend
  npm run build
  cd ..

  cd backend
  uv add gunicorn
  uv run pytest tests/test_healthz.py
  cd ..
  ```
- **(4) Verification criteria:**
  - `frontend/dist/` output size is optimized with no chunk exceeding 500kB warning.
  - Gunicorn spawns async Uvicorn workers and serves `/healthz` successfully with sub-5ms response time.
- **(5) Conventional Commit message:**
  `chore(build): configure gunicorn uvicorn workers and vite bundle optimization`

---

## PART 3: DEPLOYMENT AND LAUNCH (Steps 16–20)

### Step 16: Backend Containerization & Render Blueprint
- **(1) Objective:** Author a multi-stage production Dockerfile leveraging `uv` for fast, lightweight image builds. Create `render.yaml` infrastructure-as-code specifying service environment, health check path (`/healthz`), pre-deploy migration commands, and memory limits for Render free tier.
- **(2) Files to create/modify:**
  - `backend/Dockerfile` (Multi-stage build with `astral-sh/uv:python3.12-bookworm-slim`)
  - `backend/.dockerignore`
  - `backend/render.yaml`
  - `backend/README.md` (Backend run & deploy instructions)
- **(3) Commands:**
  ```powershell
  cd backend
  # Validate Dockerfile syntax
  docker build -t ledgerpilot-backend:test .
  docker run --rm -p 8000:8000 -e ENVIRONMENT=test ledgerpilot-backend:test curl -f http://localhost:8000/healthz
  cd ..
  ```
- **(4) Verification criteria:**
  - Docker container builds under 300MB image footprint.
  - Container spins up and responds `{"status": "healthy"}` on `/healthz`.
- **(5) Conventional Commit message:**
  `ci(render): create uv-based multi-stage dockerfile and render blueprint`

---

### Step 17: Frontend Vercel Deployment Configuration
- **(1) Objective:** Configure Vercel deployment pipeline: write `vercel.json` defining SPA client-side route rewrites, asset caching headers, and environment variable bindings for Clerk publishable key and backend API URL.
- **(2) Files to create/modify:**
  - `frontend/vercel.json`
  - `frontend/src/config/env.ts` (Strict runtime environment parsing)
  - `frontend/README.md`
- **(3) Commands:**
  ```powershell
  cd frontend
  npm run build
  npx vercel build
  cd ..
  ```
- **(4) Verification criteria:**
  - `vercel.json` correctly routes `/api/*` proxies if needed or points to Render URL.
  - Deep client-side routes (e.g., `/invoices/inv_123`) resolve to `index.html` without 404s.
- **(5) Conventional Commit message:**
  `ci(vercel): configure vercel spa routing rewrites and build pipeline`

---

### Step 18: Cross-Origin Integration, SSE Proxying & Domain Verification
- **(1) Objective:** Wire end-to-end communication between Vercel frontend domain and Render backend domain. Ensure CORS headers (`Access-Control-Allow-Origin`, `Access-Control-Allow-Headers`) and SSE streaming headers pass through Cloudflare/Render reverse proxies without payload buffering or socket drops.
- **(2) Files to create/modify:**
  - `backend/app/main.py` (Allowed origins configuration)
  - `frontend/src/lib/api-client.ts`
  - `frontend/src/lib/sse-client.ts`
  - `backend/tests/test_cors.py`
- **(3) Commands:**
  ```powershell
  cd backend
  uv run pytest tests/test_cors.py
  cd ..
  ```
- **(4) Verification criteria:**
  - OPTIONS preflight requests return 200 with appropriate CORS headers for Vercel origin.
  - SSE connections remain open past 60s without proxy dropouts.
- **(5) Conventional Commit message:**
  `feat(networking): configure cross-origin cors headers and sse proxy durability`

---

### Step 19: Live Production Smoke Tests with Realistic Sample Invoices
- **(1) Objective:** Execute automated and manual smoke tests against live Render and Vercel deployments using authentic synthetic multi-page invoice PDFs. Validate the full live lifecycle: Clerk authentication -> upload -> Groq vision extraction -> 3-way match against Supabase DB -> SSE update -> approval action.
- **(2) Files to create/modify:**
  - `backend/scripts/smoke_test_live.py` (Script sending requests against live URLs)
  - `docs/SMOKE_TEST_REPORT.md` (Logs of execution timings, latency, and status codes)
- **(3) Commands:**
  ```powershell
  cd backend
  uv run python scripts/smoke_test_live.py --target-url https://ledgerpilot-api.onrender.com
  cd ..
  ```
- **(4) Verification criteria:**
  - Live API responds with 200 OK on all endpoints.
  - Groq vision API extracts invoice fields in under 2.5 seconds.
  - Live Supabase records update and match confidence score calculates correctly.
- **(5) Conventional Commit message:**
  `test(smoke): execute live production smoke tests against render and vercel`

---

### Step 20: Comprehensive Documentation, ASCII System Architecture & ATS Resume Metrics
- **(1) Objective:** Produce production-grade root `README.md` featuring project badges, clean ASCII architecture diagram, interactive features walkthrough, API documentation, evaluation results table comparing extraction latency & match accuracy, and quantified, ATS-optimized portfolio resume bullets.
- **(2) Files to create/modify:**
  - `README.md`
  - `docs/ARCHITECTURE.md`
  - `docs/EVAL_METRICS.md`
- **(3) Commands:**
  ```powershell
  # Validate markdown formatting and link integrity
  git status
  ```
- **(4) Verification criteria:**
  - Documentation accurately reflects system architecture, test commands, and live URLs.
  - Resume bullets use strictly measured metrics (e.g., "$<1.8s$ extraction latency via Groq LPU", "99.4% 3-way match precision across 4 tolerance parameters").
- **(5) Conventional Commit message:**
  `docs(readme): add enterprise documentation, ascii diagrams, eval metrics, and resume bullets`

---

## Execution Gates & Discipline
- **Execution Mode:** Steps will be performed strictly one-by-one.
- **Gate Protocol:** For each step, implementation and tests will run to completion. Results will be shown, a conventional commit will be recorded, changes will be pushed to `origin main`, and execution will halt until the user commands **"GO"**. No failing tests will ever be committed.
