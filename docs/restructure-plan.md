# Apply-Agent Restructure Plan

*Version 1.0 — 2026-05-21*

---

## 1. Motivation

The current implementation has several UX and performance bottlenecks:

- **Slow first request**: The Qwen LLM (+ LoRA adapter) and SentenceTransformer embedding model are loaded lazily on the first `/jobs/evaluate` call, causing a multi-minute startup delay.
- **No real-time feedback**: After submitting a job, users see only a spinner — no visibility into document generation progress.
- **No editing before PDF**: Documents compile to PDF in the background with no preview or editing step.
- **Limited workflow statuses**: Only `pending | accepted | rejected`. Users need `ghosted`, `interview`, and `accepted` with the ability to change status over time.
- **No Interview page**: The `/interview` route is a stub.

---

## 2. Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Streaming transport** | Server-Sent Events (SSE) | Simpler than WebSocket; native `EventSource` support; works with HTTP/1.1; sufficient for unidirectional token streaming |
| **Editing experience** | Markdown editor | Users edit generated content in a Markdown editor; content is converted to LaTeX on confirmation via template injection |
| **Interview page scope** | List view only (for now) | Shows interview-status applications with document access. RAG-based interview prep features will be added in a future phase |
| **Database migration** | Delete & recreate | SQLite schema changes handled by dropping the DB file; `init_db()` recreates on startup |

---

## 3. Architecture Overview

```
┌──────────────────────────────────────────────────────────────────┐
│                        FastAPI Lifespan                          │
│                                                                  │
│  ┌─────────────────┐  ┌──────────────────┐  ┌────────────────┐  │
│  │  QwenAdapter     │  │ SentenceTransf.  │  │ DomainEmbedding│  │
│  │  (LLM + LoRA)   │  │  Adapter         │  │   Manager      │  │
│  └────────┬────────┘  └────────┬─────────┘  └───────┬────────┘  │
│           └──────────┬─────────┴────────────────────┘           │
│                      │                                           │
│              model_registry.py (singleton)                       │
└──────────────────────┬───────────────────────────────────────────┘
                       │ injected via Depends
    ┌──────────────────┼──────────────────────────┐
    │                  │                          │
    ▼                  ▼                          ▼
┌────────┐    ┌──────────────┐         ┌──────────────────┐
│job_router│   │stream_router │         │interview_router  │
│          │   │ (SSE)        │         │                  │
└────┬─────┘   └──────┬───────┘         └────────┬─────────┘
     │                │                          │
     ▼                ▼                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    JobMatchService                           │
│  - evaluate_job()                                           │
│  - generate_documents_stream()   ← NEW (yields tokens)     │
│  - confirm_and_compile()         ← NEW (markdown→LaTeX→PDF)│
│  - update_workflow_status()      ← EXPANDED statuses       │
└─────────────────────────────────────────────────────────────┘
```

### Frontend Flow

```
[Add Job Modal] → POST /jobs/evaluate (scores returned instantly)
       │
       ▼
[DocumentEditor Page]  ← SSE stream from POST /jobs/generate-stream
  ┌─────────────────────────────────┐
  │  Left Panel: CV (Markdown)      │   ← Tokens stream in real-time
  │  Right Panel: Cover Letter (MD) │   ← Tokens stream in real-time
  │                                 │
  │  [editable after generation]    │   ← Markdown editor mode
  │                                 │
  │  [Confirm & Generate PDF]       │   → POST /jobs/{id}/confirm
  │  [Cancel]                       │     (markdown → LaTeX → PDF)
  └─────────────────────────────────┘
       │
       ▼
[Applications List]  ← Status badges: pending|interview|accepted|rejected|ghosted
       │
       │ (status → "interview")
       ▼
[Interview Prep Page] ← Lists all interview-status applications
```

---

## 4. Implementation Phases

### Phase 1 — Eager Model & Embedding Loading

**Goal**: Load all ML models during FastAPI startup so the first user request is fast.

**Steps**:

1. Create `src/backend/model_registry.py`:
   - Module-level singletons for `QwenAdapter`, `SentenceTransformerAdapter`, `DomainEmbeddingManager`
   - `async initialize()` — loads all models via `asyncio.to_thread()` to avoid blocking the event loop
   - Getter functions: `get_llm()`, `get_embedder()`, `get_domain_manager()`
   - `is_ready() -> bool` — returns whether all models are loaded

2. Modify `src/backend/main.py`:
   - In the `lifespan()` context manager, call `await model_registry.initialize()` after `init_db()`
   - Update `/health` to report `models_ready`

3. Modify `src/backend/api/job_router.py`:
   - Update `_make_service()` to inject pre-loaded models from `model_registry`

4. Modify `src/backend/AI/llm/job_match_service.py`:
   - Remove lazy instantiation of `SentenceTransformerAdapter()` and `QwenAdapter()` in `__init__()`
   - Require explicit injection from the router

---

### Phase 2 — SSE Streaming for Document Generation

**Goal**: Stream generated CV and cover letter text to the frontend token-by-token.

**Steps**:

1. Add `generate_stream()` to `src/backend/AI/llm/llm_interface.py`:
   - Uses `transformers.TextIteratorStreamer` with `skip_prompt=True`
   - Launches generation in a thread, yields tokens from the streamer

2. Create `src/backend/api/stream_router.py`:
   - `POST /jobs/generate-stream` — SSE endpoint
   - Events: `cv_token`, `cv_complete`, `cover_token`, `cover_complete`, `error`
   - Saves generated markdown text to DB columns `cv_text`, `cover_letter_text`
   - Sets `processing = False` when done

3. Register the router in `main.py`

---

### Phase 3 — Updated Data Model & Confirm Flow

**Goal**: Expand the data model, add new statuses, and create the confirm-to-PDF flow.

**Steps**:

1. Modify `src/backend/models/job_application.py`:
   - Add columns: `confirmed (bool)`, `cv_text (Text)`, `cover_letter_text (Text)`
   - Document expanded `workflow_status`: `pending | ghosted | rejected | interview | accepted`

2. Modify `src/backend/schemas/job_schemas.py`:
   - Update all `Literal` types to include new statuses
   - Add `JobConfirmIn`, `JobDocumentUpdate` schemas
   - Update `JobApplicationListOut` with new fields

3. Create LaTeX templates:
   - `src/backend/utils/latex_templates/cv_template.tex`
   - `src/backend/utils/latex_templates/cover_letter_template.tex`

4. Modify `src/backend/utils/latex_renderer.py`:
   - Add `render_from_markdown()` — converts markdown to LaTeX-safe text, injects into template, compiles PDF

5. Add endpoints to `src/backend/api/job_router.py`:
   - `POST /jobs/{job_id}/confirm` — markdown → LaTeX → PDF
   - `PATCH /jobs/{job_id}/documents` — save edited markdown (auto-save)

6. Delete the SQLite database file to trigger schema recreation on next startup

---

### Phase 4 — Interview Page Backend

**Goal**: API endpoints for the interview page.

**Steps**:

1. Create `src/backend/api/interview_router.py`:
   - `GET /interviews` — returns all jobs with `workflow_status == "interview"`
   - `GET /interviews/{job_id}` — returns full job detail

2. Register in `main.py`

3. Update `src/backend/routers/dashboard.py`:
   - Count interview-status jobs for `interview_sessions` stat

---

### Phase 5 — Frontend: Document Editor with Streaming

**Goal**: Build the real-time document generation and markdown editing UI.

**Steps**:

1. Update `src/frontend/src/services/api.ts`:
   - `streamGenerateDocuments()` — SSE client using `fetch` + `ReadableStream`
   - `confirmJob()` — POST confirm endpoint
   - `updateJobDocuments()` — PATCH auto-save
   - `getInterviews()` — GET interviews
   - Update status type to include new values

2. Create `DocumentEditor.tsx` + `DocumentEditor.css`:
   - Split-panel layout (CV left, Cover Letter right)
   - Streaming text display with typing cursor animation
   - Markdown editor (textarea with markdown preview) after generation completes
   - "Confirm & Generate PDF" button → loading overlay → redirect to applications list
   - "Cancel" button

3. Modify `Applications.tsx` + `Applications.css`:
   - Navigate to `/applications/{jobId}/edit` after evaluation
   - Status dropdown on each job card (5 options)
   - Color-coded status badges
   - Show download buttons only when `confirmed === true`
   - Fix all padding issues

---

### Phase 6 — Frontend: Interview Prep Page

**Goal**: Replace the interview stub with a real page.

**Steps**:

1. Create `Interviews.tsx` + `Interviews.css`:
   - Fetch from `GET /interviews`
   - Job cards with: company, title, match score, status badge, document downloads
   - Empty state: "No interviews scheduled yet"

2. Modify `App.tsx`:
   - Import and use `Interviews` component for `/interview` route
   - Add `/applications/:jobId/edit` route for `DocumentEditor`

---

### Phase 7 — Testing & Polish

**Steps**:

1. Backend unit tests:
   - `model_registry.py` (mocked loads)
   - SSE streaming endpoint
   - Confirm endpoint
   - Interview endpoints
   - Workflow status transitions

2. Frontend tests:
   - `DocumentEditor` component
   - `Interviews` page

3. End-to-end manual verification:
   - Startup → model loading → fast first request
   - Submit job → streaming → edit → confirm → download PDF
   - Status changes → interview page updates
   - Padding/spacing audit

---

## 5. File Inventory

### New Files
| File | Purpose |
|------|---------|
| `src/backend/model_registry.py` | Singleton model loader |
| `src/backend/api/stream_router.py` | SSE streaming endpoint |
| `src/backend/api/interview_router.py` | Interview page API |
| `src/backend/utils/latex_templates/cv_template.tex` | CV LaTeX template |
| `src/backend/utils/latex_templates/cover_letter_template.tex` | Cover letter LaTeX template |
| `src/frontend/src/pages/Applications/DocumentEditor.tsx` | Streaming editor page |
| `src/frontend/src/pages/Applications/DocumentEditor.css` | Editor styling |
| `src/frontend/src/pages/Interviews/Interviews.tsx` | Interview list page |
| `src/frontend/src/pages/Interviews/Interviews.css` | Interview styling |

### Modified Files
| File | Changes |
|------|---------|
| `src/backend/main.py` | Eager model loading, new routers |
| `src/backend/AI/llm/llm_interface.py` | Add `generate_stream()` |
| `src/backend/AI/llm/job_match_service.py` | Require injected models, new methods |
| `src/backend/api/job_router.py` | New endpoints, model injection |
| `src/backend/models/job_application.py` | New columns, expanded statuses |
| `src/backend/schemas/job_schemas.py` | New schemas, expanded Literals |
| `src/backend/utils/latex_renderer.py` | Markdown→LaTeX rendering |
| `src/backend/routers/dashboard.py` | Interview count |
| `src/frontend/src/services/api.ts` | New API calls, SSE client |
| `src/frontend/src/App.tsx` | New routes |
| `src/frontend/src/pages/Applications/Applications.tsx` | Status dropdowns, navigation |
| `src/frontend/src/pages/Applications/Applications.css` | Padding fixes, badges |

---

## 6. Risk & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| Model download on first startup (~3 GB) | Long first startup | Log progress; cache persists after first download |
| pdflatex not installed | PDF compilation fails | Clear error message; graceful fallback (return LaTeX source) |
| SSE connection drops | Partial document | Frontend reconnection logic; save partial text to DB |
| Markdown→LaTeX conversion edge cases | Broken PDFs | Sanitize markdown; escape LaTeX special chars; robust templates |
