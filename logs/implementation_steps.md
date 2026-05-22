# Apply-Agent Restructure — Step-by-Step Implementation Guide

*Created: 2026-05-21 | Session: restructure_phase*

---

## Overview

This document provides a detailed, step-by-step task breakdown for restructuring the Apply-Agent application. Each task includes the exact files to modify, what to change, and the order of operations.

---

## Phase 1: Eager Model & Embedding Loading at Startup

### Goal
Load the Qwen LLM (+ LoRA adapter) and the SentenceTransformer embedding model during the FastAPI `lifespan` startup event, so they're warm and ready when the first user request arrives.

### Tasks

- [ ] **1.1** Create `src/backend/model_registry.py`
  - Define module-level variables: `_llm`, `_embedder`, `_domain_manager` (all initially `None`)
  - Implement `async initialize()`:
    - Use `asyncio.to_thread()` to load `QwenAdapter()` (heavy — downloads base model + LoRA)
    - Use `asyncio.to_thread()` to load `SentenceTransformerAdapter()`
    - Use `asyncio.to_thread()` to load `DomainEmbeddingManager()`
    - Store in module-level variables
    - Log timing for each load
  - Implement `get_llm() -> QwenAdapter`
  - Implement `get_embedder() -> SentenceTransformerAdapter`
  - Implement `get_domain_manager() -> DomainEmbeddingManager`
  - Implement `is_ready() -> bool`

- [ ] **1.2** Modify `src/backend/main.py`
  - Import `model_registry`
  - In `lifespan()`, after `await init_db()`, add `await model_registry.initialize()`
  - Update `/health` to include `models_ready: model_registry.is_ready()`

- [ ] **1.3** Modify `src/backend/api/job_router.py`
  - Update `_make_service(db)` to pass `model_registry.get_llm()` and `model_registry.get_embedder()` to `JobMatchService()`
  - Remove any inline model instantiation

- [ ] **1.4** Modify `src/backend/AI/llm/job_match_service.py`
  - In `__init__()`, change defaults: `embedding_adapter=None` and `llm=None` should now raise if not provided (require explicit injection)
  - Or keep defaults but log a warning that lazy loading is being used

- [ ] **1.5** Test eager loading
  - Start the app, verify console shows model loading messages
  - Verify `/health` returns `models_ready: true`
  - Verify first `/jobs/evaluate` call is fast (no model loading delay)

---

## Phase 2: SSE Streaming for Document Generation

### Goal
After evaluation, stream the generated CV and cover letter text to the frontend token-by-token using Server-Sent Events.

### Tasks

- [ ] **2.1** Add streaming to `src/backend/AI/llm/llm_interface.py`
  - Import `TextIteratorStreamer` from `transformers`
  - Add `generate_stream(prompt: str) -> Generator[str, None, None]` to `QwenAdapter`:
    - Create a `TextIteratorStreamer` with `skip_prompt=True`
    - Launch `model.generate()` in a separate thread
    - Yield tokens from the streamer

- [ ] **2.2** Create `src/backend/api/stream_router.py`
  - `POST /jobs/generate-stream` endpoint
  - Accept `{ job_id: str }` body
  - Verify job exists and has been evaluated
  - Use `StreamingResponse` with `media_type="text/event-stream"`
  - Build CV prompt → stream tokens as `event: cv_token\ndata: {"token": "..."}\n\n`
  - Send `event: cv_complete\ndata: {"text": "full cv text"}\n\n`
  - Build cover letter prompt → stream tokens as `event: cover_token\ndata: {"token": "..."}\n\n`
  - Send `event: cover_complete\ndata: {"text": "full cover letter text"}\n\n`
  - Save generated text to DB (`cv_text`, `cover_letter_text` columns)
  - Set `processing = False`

- [ ] **2.3** Register router in `src/backend/main.py`
  - Import and include `stream_router`

- [ ] **2.4** Test SSE endpoint
  - Use `curl` to test: `curl -N -X POST http://localhost:8000/jobs/generate-stream -d '{"job_id":"..."}'`
  - Verify tokens arrive incrementally
  - Verify `cv_complete` and `cover_complete` events are sent

---

## Phase 3: Updated Data Model & Confirm Flow

### Goal
Add new columns to the `JobApplication` model, expand workflow statuses, and create the "confirm" endpoint that compiles PDFs.

### Tasks

- [ ] **3.1** Modify `src/backend/models/job_application.py`
  - Add `confirmed: Mapped[bool] = mapped_column(Boolean, default=False)`
  - Add `cv_text: Mapped[str | None] = mapped_column(Text, nullable=True)`
  - Add `cover_letter_text: Mapped[str | None] = mapped_column(Text, nullable=True)`
  - Expand `workflow_status` comment to document: `pending | ghosted | rejected | interview | accepted`

- [ ] **3.2** Modify `src/backend/schemas/job_schemas.py`
  - Update `WorkflowStatusUpdate.status` Literal: `"pending" | "accepted" | "rejected" | "interview" | "ghosted"`
  - Update `JobEvaluationOut.workflow_status` Literal similarly
  - Update `JobStatusOut.workflow_status` Literal similarly
  - Add `JobConfirmIn(BaseModel)`:
    - `cv_text: str`
    - `cover_letter_text: str`
  - Add `JobDocumentUpdate(BaseModel)`:
    - `cv_text: str | None = None`
    - `cover_letter_text: str | None = None`
  - Update `JobApplicationListOut` to add: `confirmed: bool`, `cv_text: str | None`, `cover_letter_text: str | None`

- [ ] **3.3** Create LaTeX templates
  - Create `src/backend/utils/latex_templates/cv_template.tex` — professional CV template with `{{CONTENT}}` placeholder
  - Create `src/backend/utils/latex_templates/cover_letter_template.tex` — professional cover letter template

- [ ] **3.4** Modify `src/backend/utils/latex_renderer.py`
  - Add `render_from_text(text, template_type, job_id, user_info)` method:
    - Load the appropriate `.tex` template
    - Escape special LaTeX characters in the text
    - Replace `{{CONTENT}}` with the escaped text
    - Fill in user info placeholders (name, email, phone)
    - Compile to PDF using existing `_run_pdflatex`
    - Return PDF path

- [ ] **3.5** Add endpoints to `src/backend/api/job_router.py`
  - `POST /jobs/{job_id}/confirm`:
    - Accept `JobConfirmIn` body
    - Save `cv_text` and `cover_letter_text`
    - Call `latex_renderer.render_from_text()` for CV
    - Call `latex_renderer.render_from_text()` for cover letter
    - Set `confirmed = True`, `processing = False`
    - Return download URLs
  - `PATCH /jobs/{job_id}/documents`:
    - Accept `JobDocumentUpdate` body
    - Save `cv_text` and/or `cover_letter_text`
    - Return success

- [ ] **3.6** Update `PATCH /jobs/{job_id}/status`
  - Accept new status values
  - No special logic needed for status change (interview filter is handled by the interview endpoint)

- [ ] **3.7** Update `list_jobs` endpoint
  - Include new fields in response

- [ ] **3.8** Delete the database file to trigger schema recreation
  - Or run manual ALTER TABLE statements
  - SQLite does not support `ALTER TABLE ADD COLUMN` for multiple columns in one statement, so each needs a separate call

---

## Phase 4: Interview Page Backend

### Goal
Create API endpoints for the interview page that returns job applications with `workflow_status == "interview"`.

### Tasks

- [ ] **4.1** Create `src/backend/api/interview_router.py`
  - `GET /interviews` — query `JobApplication` where `workflow_status == "interview"`, order by `updated_at desc`
  - `GET /interviews/{job_id}` — return full job detail including documents
  - Return using existing schemas (or a new `InterviewListOut` schema)

- [ ] **4.2** Register in `src/backend/main.py`
  - Import and include `interview_router`

- [ ] **4.3** Update `src/backend/routers/dashboard.py`
  - Count `workflow_status == "interview"` for `interview_sessions`

- [ ] **4.4** Test interview endpoints
  - Create a job, set status to "interview"
  - Verify `GET /interviews` returns it
  - Verify dashboard stats update

---

## Phase 5: Frontend — Document Editor with Streaming

### Goal
Build the real-time document generation and editing UI.

### Tasks

- [ ] **5.1** Update `src/frontend/src/services/api.ts`
  - Add `streamGenerateDocuments(jobId, onCvToken, onCoverToken, onComplete)`:
    - Use `fetch()` with `ReadableStream` to parse SSE events
    - Call callbacks for each token type
  - Add `confirmJob(jobId, cvText, coverLetterText)` → `POST /jobs/{id}/confirm`
  - Add `updateJobDocuments(jobId, cvText, coverLetterText)` → `PATCH /jobs/{id}/documents`
  - Add `getInterviews()` → `GET /interviews`
  - Update `updateJobStatus` to accept new status values

- [ ] **5.2** Create `DocumentEditor.tsx` and `DocumentEditor.css`
  - Two-panel layout (CV left, Cover Letter right)
  - Streaming text display with typing cursor animation
  - Transition to editable `<textarea>` when generation completes
  - "Confirm & Generate PDF" primary button
  - "Cancel" secondary button
  - Loading overlay during PDF compilation
  - Auto-save with debounce on text changes

- [ ] **5.3** Modify `src/frontend/src/pages/Applications/Applications.tsx`
  - After successful `evaluateJob()`, navigate to `/applications/{jobId}/edit`
  - Add status dropdown to each job card (select with the 5 status options)
  - Color-coded status badges:
    - `pending` → gray
    - `interview` → blue
    - `accepted` → green
    - `rejected` → red
    - `ghosted` → dark/muted
  - Show "Download CV" and "Download Cover Letter" only when `confirmed === true`
  - Fix all padding issues

- [ ] **5.4** Update `src/frontend/src/pages/Applications/Applications.css`
  - Fix padding throughout
  - Add status badge colors
  - Responsive grid adjustments

---

## Phase 6: Frontend — Interview Prep Page

### Goal
Replace the Interview Prep stub with a real page.

### Tasks

- [ ] **6.1** Create `src/frontend/src/pages/Interviews/Interviews.tsx`
  - Fetch from `GET /interviews`
  - List job cards showing: company, title, match score, status badge
  - Download buttons for CV and Cover Letter PDF
  - Empty state: "No interviews scheduled yet"

- [ ] **6.2** Create `src/frontend/src/pages/Interviews/Interviews.css`
  - Consistent styling with Applications page

- [ ] **6.3** Modify `src/frontend/src/App.tsx`
  - Import `Interviews` component
  - Replace Stub for `/interview` route
  - Add `/applications/:jobId/edit` route for `DocumentEditor`

---

## Phase 7: Testing & Polish

### Tasks

- [ ] **7.1** Backend unit tests for `model_registry.py` (mocked model loads)
- [ ] **7.2** Backend unit tests for SSE streaming endpoint
- [ ] **7.3** Backend unit tests for `/jobs/{id}/confirm`
- [ ] **7.4** Backend unit tests for `/interviews` endpoints
- [ ] **7.5** Backend unit tests for workflow status transitions
- [ ] **7.6** Frontend tests for `DocumentEditor` component
- [ ] **7.7** Frontend tests for `Interviews` page
- [ ] **7.8** End-to-end manual test:
  - Start app → verify models load on startup
  - Submit job → see streaming generation → edit → confirm → download PDF
  - Change status to interview → verify interview page
  - Change status to ghosted/rejected → verify badge updates
- [ ] **7.9** Fix all remaining padding/spacing issues
- [ ] **7.10** Update session log and `memory.md`

---

## Execution Order

```
Phase 1 (Eager Loading) → Phase 2 (SSE Streaming) → Phase 3 (Data Model + Confirm Flow)
         ↓                                                          ↓
Phase 4 (Interview Backend) ← ← ← ← ← ← ← ← ← ← ← ← ← ← ← ←
         ↓
Phase 5 (Frontend Editor) → Phase 6 (Interview Page) → Phase 7 (Testing & Polish)
```

Phases 1–3 are sequential (each depends on the previous). Phase 4 can happen in parallel with Phase 3. Phases 5–6 depend on all backend phases. Phase 7 is the final pass.
