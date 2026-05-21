# Apply-Agent: AI Career Assistant Desktop Application

A local-first, AI-powered career assistant built with Tauri (React + TypeScript frontend) and Python (FastAPI backend), featuring persistent memory, contextual RAG workflows, and intelligent document generation.

---

## User Review Required

> [!NOTE]
> **Rust/Cargo** -- Confirmed installed at `C:\Users\Amine\.cargo\bin` (rustc 1.95.0, cargo 1.95.0)

> [!NOTE]
> **LaTeX engine** -- Confirmed installed (MiKTeX-pdfTeX 4.23)

> [!NOTE]
> **Python environment** -- Using conda `agents` env at `C:\Users\Amine\miniconda3\envs\agents` (Python 3.11.15)

> [!WARNING]
> **Your `.env` file contains an API key that is tracked by git** (though `.env` is in `.gitignore`). The current `API_KEY` value appears to be a BLS API key used by `scrapper.py`. I will preserve it and add new config variables alongside it.

---

## Open Questions

> [!NOTE]
> **State management:** Using **Zustand** (confirmed by user).

> [!NOTE]
> **LLM integration:** Using **Qwen** (extremely small model) via **LangChain** library. The architecture remains modular so this can be swapped for the fine-tuned model later.

> [!NOTE]
> **TailwindCSS version:** Using **v4** (CSS-first config, latest).

---

## Existing Codebase Analysis

### What exists today

| Component | Status | Files |
|-----------|--------|-------|
| FastAPI server | Basic, functional | `src/backend/main.py` |
| CV parser (regex-based) | Complete | `AI/raw_cv_parser.py` |
| CV processor + embeddings | Complete | `AI/cv_processor.py`, `AI/domain_embeddings.py` |
| Cover letter generator | Partial (needs LLM) | `AI/cover_letter_generator.py` |
| RAG data scraper | Complete | `scrapper.py` |
| Frontend | **Empty** (placeholder README only) | `src/front/README.md` |
| Database/persistence | **None** | -- |
| Tauri wrapper | **None** | -- |
| Job matching/scoring | **None** | -- |
| Interview module | **None** | -- |
| Templates (LaTeX) | **None** (inline in cover_letter_generator) | -- |

### What will be preserved
- All existing `AI/` modules (cv_processor, domain_embeddings, raw_cv_parser, cover_letter_generator)
- CV examples and cover letter instruction data
- RAG raw data pipeline (`scrapper.py`)
- The `launch.py` script (will be updated)
- The `.env` configuration

---

## Proposed Architecture

```
Apply-Agent/
├── src/
│   ├── frontend/                    # Tauri + React + TypeScript
│   │   ├── src-tauri/               # Tauri Rust config
│   │   ├── src/
│   │   │   ├── components/          # React components
│   │   │   ├── pages/               # Page-level views
│   │   │   ├── stores/              # Zustand stores
│   │   │   ├── hooks/               # Custom hooks
│   │   │   ├── services/            # API client layer
│   │   │   ├── types/               # TypeScript types
│   │   │   └── styles/              # Design tokens
│   │   ├── index.html
│   │   ├── tailwind.config.ts
│   │   └── package.json
│   │
│   └── backend/                     # Python FastAPI
│       ├── main.py                  # FastAPI app entry
│       ├── config.py                # Settings/env
│       ├── database.py              # SQLite + SQLAlchemy
│       ├── models/                  # SQLAlchemy ORM models
│       ├── routers/                 # FastAPI route modules
│       ├── services/                # Business logic
│       ├── AI/                      # Existing + new AI modules
│       │   ├── llm/                 # LLM interface layer
│       │   │   ├── base.py          # Abstract LLM interface
│       │   │   ├── placeholder.py   # Mock LLM implementation
│       │   │   └── provider.py      # LLM factory
│       │   ├── scoring/             # Job matching
│       │   │   ├── job_matcher.py
│       │   │   ├── llm_scorer.py
│       │   │   └── scoring_pipeline.py
│       │   ├── interview/           # Interview prep
│       │   │   ├── interview_rag.py
│       │   │   ├── interview_context_builder.py
│       │   │   └── mock_interviewer.py
│       │   ├── embeddings/          # RAG/vector search
│       │   │   ├── embedding_service.py
│       │   │   ├── vector_store.py
│       │   │   └── rag_pipeline.py
│       │   ├── cv_processor.py      # Existing
│       │   ├── domain_embeddings.py # Existing
│       │   ├── raw_cv_parser.py     # Existing
│       │   └── cover_letter_generator.py # Existing (refactored)
│       ├── templates/               # LaTeX templates
│       │   ├── cv/
│       │   │   └── professional.tex
│       │   └── cover_letter/
│       │       └── standard.tex
│       └── requirements.txt
│
├── data/                            # SQLite DB + vector indices
├── docs/                            # Documentation
├── launch.py                        # Root launcher
└── .env
```

---

## Proposed Changes

### Phase 1: Project Scaffolding and Infrastructure

Estimated scope: Foundation setup -- Tauri app, React project, TailwindCSS, design system, backend restructuring.

---

#### Prerequisites

Install Rust toolchain (required for Tauri):
```powershell
# User must run: winget install Rustlang.Rustup
# Or download from https://rustup.rs/
```

---

#### Frontend Scaffolding

##### [NEW] Tauri + Vite + React + TypeScript project

Initialize in `src/frontend/` using `npm create tauri-app`:
- Vite as bundler
- React + TypeScript template
- TailwindCSS v4 integration
- Bootstrap Icons via `bootstrap-icons` npm package

##### [NEW] [tailwind.config.ts](file:///c:/Users/Amine/Desktop/Apply/Apply-Agent/src/frontend/tailwind.config.ts)
Custom design tokens:
- Color palette (neutral grays, single accent color, dark/light themes)
- Typography scale (Inter font family)
- Spacing scale
- No gradients, no shadows heavier than `shadow-sm`

##### [NEW] [src/styles/globals.css](file:///c:/Users/Amine/Desktop/Apply/Apply-Agent/src/frontend/src/styles/globals.css)
- CSS custom properties for theming
- Dark/light mode via `prefers-color-scheme` + manual toggle
- Base typography and reset styles

##### [NEW] [src/stores/themeStore.ts](file:///c:/Users/Amine/Desktop/Apply/Apply-Agent/src/frontend/src/stores/themeStore.ts)
Zustand store for theme persistence (dark/light)

##### [NEW] [src/services/api.ts](file:///c:/Users/Amine/Desktop/Apply/Apply-Agent/src/frontend/src/services/api.ts)
Typed API client wrapping `fetch` for communicating with the FastAPI backend

---

#### Backend Restructuring

##### [MODIFY] [main.py](file:///c:/Users/Amine/Desktop/Apply/Apply-Agent/src/backend/main.py)
- Refactor into modular router-based architecture
- Add CORS middleware for Tauri frontend
- Add lifespan events for DB initialization
- Import routers instead of defining all endpoints inline

##### [NEW] [config.py](file:///c:/Users/Amine/Desktop/Apply/Apply-Agent/src/backend/config.py)
- Pydantic Settings class reading from `.env`
- Database path, LLM config, embedding model config

##### [NEW] [database.py](file:///c:/Users/Amine/Desktop/Apply/Apply-Agent/src/backend/database.py)
- SQLAlchemy async engine with SQLite (aiosqlite)
- Session factory
- Base model class
- Auto-create tables on startup

##### [NEW] [models/](file:///c:/Users/Amine/Desktop/Apply/Apply-Agent/src/backend/models/)
SQLAlchemy ORM models:
- `user_profile.py` -- user context, skills, preferences
- `cv.py` -- CV versions, content, metadata
- `cover_letter.py` -- generated cover letters
- `job_application.py` -- job sessions, descriptions, status
- `interview.py` -- interview sessions, Q&A history
- `document.py` -- uploaded documents
- `conversation.py` -- AI chat history

##### [NEW] [routers/](file:///c:/Users/Amine/Desktop/Apply/Apply-Agent/src/backend/routers/)
FastAPI routers (one per domain):
- `profile.py` -- user profile CRUD
- `cv.py` -- CV generation, editing, versioning
- `cover_letter.py` -- cover letter generation
- `job_application.py` -- job workflow endpoints
- `interview.py` -- interview prep endpoints
- `dashboard.py` -- aggregated stats
- `onboarding.py` -- onboarding flow endpoints

---

#### [MODIFY] [launch.py](file:///c:/Users/Amine/Desktop/Apply/Apply-Agent/launch.py)
Update paths from `src/front` to `src/frontend`, add Tauri dev launch option

#### [MODIFY] [.gitignore](file:///c:/Users/Amine/Desktop/Apply/Apply-Agent/.gitignore)
Add: `node_modules/`, `dist/`, `target/`, `data/*.db`, `*.pyc`, `__pycache__/`, `.venv/`

---

### Phase 2: Persistence and User Context System

Estimated scope: SQLite database, user profile, onboarding flow backend + frontend.

---

#### Backend Services

##### [NEW] [services/profile_service.py](file:///c:/Users/Amine/Desktop/Apply/Apply-Agent/src/backend/services/profile_service.py)
- Create/update user profile
- Parse uploaded CV into structured profile
- Store experience, education, skills, certifications, languages, achievements, career goals
- Version tracking for profile changes

##### [NEW] [services/cv_service.py](file:///c:/Users/Amine/Desktop/Apply/Apply-Agent/src/backend/services/cv_service.py)
- Generate CV from profile + job context
- Save CV versions
- Export to LaTeX then PDF
- Edit/regenerate individual sections

##### [NEW] [services/context_service.py](file:///c:/Users/Amine/Desktop/Apply/Apply-Agent/src/backend/services/context_service.py)
- Aggregate all user context for RAG queries
- Build context windows for LLM prompts
- Manage conversation history
- Provide context for any generation task

---

#### Frontend -- Onboarding

##### [NEW] [src/pages/Onboarding/](file:///c:/Users/Amine/Desktop/Apply/Apply-Agent/src/frontend/src/pages/Onboarding/)
Multi-step onboarding flow:
1. **Welcome** -- intro screen explaining the app
2. **CV Upload** -- drag-and-drop or file picker for existing CV (PDF/DOCX/TXT)
3. **Manual Input** -- guided step-by-step for each profile section (not a giant form):
   - Work experience (conversational, one entry at a time)
   - Education
   - Projects
   - Skills (tag-based input)
   - Certifications
   - Languages
   - Achievements
   - Career goals
4. **Review** -- show parsed/entered profile in a clean card layout
5. **CV Generation** -- if no CV uploaded, auto-generate and show editable preview
6. **Complete** -- save and redirect to dashboard

##### [NEW] [src/stores/onboardingStore.ts](file:///c:/Users/Amine/Desktop/Apply/Apply-Agent/src/frontend/src/stores/onboardingStore.ts)
Zustand store for onboarding state, step tracking, form data

##### [NEW] [src/stores/profileStore.ts](file:///c:/Users/Amine/Desktop/Apply/Apply-Agent/src/frontend/src/stores/profileStore.ts)
Zustand store for persistent user profile data

---

### Phase 3: LLM Integration and Embedding System

Estimated scope: Modular LLM interface, FAISS vector store, RAG pipeline.

---

#### LLM Layer

##### [NEW] [AI/llm/base.py](file:///c:/Users/Amine/Desktop/Apply/Apply-Agent/src/backend/AI/llm/base.py)
Abstract base class:
```python
class BaseLLM(ABC):
    @abstractmethod
    async def generate(self, prompt: str, max_tokens: int = 1024) -> str: ...
    
    @abstractmethod
    async def generate_structured(self, prompt: str, schema: dict) -> dict: ...
```

##### [NEW] [AI/llm/placeholder.py](file:///c:/Users/Amine/Desktop/Apply/Apply-Agent/src/backend/AI/llm/placeholder.py)
Mock implementation returning template-based realistic responses for:
- CV section generation
- Cover letter generation  
- Interview question generation
- Job analysis

##### [NEW] [AI/llm/provider.py](file:///c:/Users/Amine/Desktop/Apply/Apply-Agent/src/backend/AI/llm/provider.py)
Factory pattern to instantiate the configured LLM backend. Single config change swaps placeholder for fine-tuned model.

---

#### Embedding and RAG

##### [NEW] [AI/embeddings/embedding_service.py](file:///c:/Users/Amine/Desktop/Apply/Apply-Agent/src/backend/AI/embeddings/embedding_service.py)
- Wraps sentence-transformers model
- Embeds: CVs, cover letters, job descriptions, interview transcripts, user profile sections
- Batch embedding support

##### [NEW] [AI/embeddings/vector_store.py](file:///c:/Users/Amine/Desktop/Apply/Apply-Agent/src/backend/AI/embeddings/vector_store.py)
- FAISS-based local vector index
- Add/remove/search operations
- Persist index to disk in `data/` directory
- Metadata storage alongside vectors

##### [NEW] [AI/embeddings/rag_pipeline.py](file:///c:/Users/Amine/Desktop/Apply/Apply-Agent/src/backend/AI/embeddings/rag_pipeline.py)
- Retrieve relevant context from vector store
- Build augmented prompts for LLM
- Reusable across all generation tasks (CV, cover letter, interview, job matching)

---

#### [MODIFY] [AI/cover_letter_generator.py](file:///c:/Users/Amine/Desktop/Apply/Apply-Agent/src/backend/AI/cover_letter_generator.py)
Refactor to use the new `BaseLLM` interface instead of raw `llm.generate()` calls

---

### Phase 4: LaTeX Template System and PDF Generation

Estimated scope: LaTeX templates, template engine, PDF compilation pipeline.

---

##### [NEW] [templates/cv/professional.tex](file:///c:/Users/Amine/Desktop/Apply/Apply-Agent/src/backend/templates/cv/professional.tex)
Professional CV LaTeX template with Jinja2-style variables:
- `{{name}}`, `{{email}}`, `{{phone}}`, `{{location}}`
- `{{summary}}`
- `{% for exp in experience %}` blocks
- `{% for edu in education %}` blocks
- Skills grid layout
- ATS-friendly formatting (no columns, no graphics)

##### [NEW] [templates/cover_letter/standard.tex](file:///c:/Users/Amine/Desktop/Apply/Apply-Agent/src/backend/templates/cover_letter/standard.tex)
Standard cover letter template with similar variable system

##### [NEW] [services/template_service.py](file:///c:/Users/Amine/Desktop/Apply/Apply-Agent/src/backend/services/template_service.py)
- List available templates
- Render templates with data (Jinja2 for LaTeX)
- Compile LaTeX to PDF via subprocess
- Template registry for future extensibility

---

### Phase 5: Job Application Workflow and Dashboard

Estimated scope: Full job application pipeline, scoring, dashboard UI.

---

#### Job Matching and Scoring

##### [NEW] [AI/scoring/job_matcher.py](file:///c:/Users/Amine/Desktop/Apply/Apply-Agent/src/backend/AI/scoring/job_matcher.py)
- Extract requirements from job description (skills, technologies, responsibilities, seniority, keywords, soft skills, ATS terms)
- Compare against user profile
- Generate structured match report

##### [NEW] [AI/scoring/llm_scorer.py](file:///c:/Users/Amine/Desktop/Apply/Apply-Agent/src/backend/AI/scoring/llm_scorer.py)
- Placeholder scoring module (for your future LLM-based scoring)
- Clean interface: `score(job_analysis, user_profile) -> ScoringResult`

##### [NEW] [AI/scoring/scoring_pipeline.py](file:///c:/Users/Amine/Desktop/Apply/Apply-Agent/src/backend/AI/scoring/scoring_pipeline.py)
- Orchestrates job_matcher + llm_scorer
- Produces final compatibility score (0-100%)
- Modular: easy to swap scoring components

---

#### Job Application Backend

##### [NEW] [services/job_application_service.py](file:///c:/Users/Amine/Desktop/Apply/Apply-Agent/src/backend/services/job_application_service.py)
- Create new job application session
- Parse job description
- Trigger parallel CV + cover letter generation (using `asyncio.create_task`)
- Save session with all artifacts
- Status management (draft, submitted, interview, archived)
- Duplicate/delete/archive operations

---

#### Frontend -- Dashboard and Job Workflow

##### [NEW] [src/pages/Dashboard/](file:///c:/Users/Amine/Desktop/Apply/Apply-Agent/src/frontend/src/pages/Dashboard/)
Dashboard page with:
- Stats cards (total generated, submitted, interview prep sessions)
- Recent activity timeline
- Active applications list with match scores
- Quick actions (new application, new interview prep)
- Application status distribution

##### [NEW] [src/pages/JobApplication/](file:///c:/Users/Amine/Desktop/Apply/Apply-Agent/src/frontend/src/pages/JobApplication/)
- **NewJob** -- paste job description, company info, notes
- **JobAnalysis** -- show extracted requirements, match score, skill gaps
- **CVEditor** -- editable generated CV with section-level regeneration
- **CoverLetterEditor** -- editable cover letter
- **JobSession** -- persistent workspace per application

##### [NEW] [src/pages/History/](file:///c:/Users/Amine/Desktop/Apply/Apply-Agent/src/frontend/src/pages/History/)
- List all applications with filters (active, archived, interview stage)
- Search and sort
- Reopen/duplicate/delete actions

##### [NEW] [src/components/Layout/](file:///c:/Users/Amine/Desktop/Apply/Apply-Agent/src/frontend/src/components/Layout/)
- `Sidebar.tsx` -- persistent navigation sidebar
- `AppShell.tsx` -- main layout wrapper
- `Header.tsx` -- minimal top bar with theme toggle

##### [NEW] [src/components/common/](file:///c:/Users/Amine/Desktop/Apply/Apply-Agent/src/frontend/src/components/common/)
Reusable UI primitives:
- `Button.tsx`, `Input.tsx`, `TextArea.tsx`, `Card.tsx`
- `Modal.tsx`, `Badge.tsx`, `Tabs.tsx`
- `ProgressBar.tsx`, `Skeleton.tsx` (loading states)
- `FileUpload.tsx`

---

### Phase 6: Interview Preparation Module

Estimated scope: Interview RAG pipeline, mock interviewer, frontend interview UI.

---

#### Interview Backend

##### [NEW] [AI/interview/interview_rag.py](file:///c:/Users/Amine/Desktop/Apply/Apply-Agent/src/backend/AI/interview/interview_rag.py)
- Build interview-specific RAG context from job description, CV, cover letter, company info, previous conversations
- Retrieve relevant past interview Q&A

##### [NEW] [AI/interview/interview_context_builder.py](file:///c:/Users/Amine/Desktop/Apply/Apply-Agent/src/backend/AI/interview/interview_context_builder.py)
- Assemble comprehensive interview preparation context
- Categorize into: technical, behavioral, HR, company-specific

##### [NEW] [AI/interview/mock_interviewer.py](file:///c:/Users/Amine/Desktop/Apply/Apply-Agent/src/backend/AI/interview/mock_interviewer.py)
- Generate mock interview questions based on context
- Evaluate user responses
- Provide coaching feedback
- Track interview session state

##### [NEW] [services/interview_service.py](file:///c:/Users/Amine/Desktop/Apply/Apply-Agent/src/backend/services/interview_service.py)
- Create interview prep session linked to job application
- Manage Q&A flow
- Save session history
- Generate prep materials

---

#### Frontend -- Interview

##### [NEW] [src/pages/Interview/](file:///c:/Users/Amine/Desktop/Apply/Apply-Agent/src/frontend/src/pages/Interview/)
- **InterviewPrep** -- select linked application, view generated prep materials
- **MockInterview** -- chat-style interface for mock Q&A
- **InterviewHistory** -- past sessions and performance

---

## UI/UX Design System

### Color Palette
```
Light Theme:
  Background:    #FAFAFA
  Surface:       #FFFFFF
  Border:        #E5E5E5
  Text Primary:  #171717
  Text Secondary:#737373
  Accent:        #2563EB (single blue accent)
  
Dark Theme:
  Background:    #0A0A0A
  Surface:       #171717
  Border:        #262626
  Text Primary:  #FAFAFA
  Text Secondary:#A3A3A3
  Accent:        #3B82F6
```

### Typography
- Font: Inter (Google Fonts)
- Sizes: 12px (xs), 14px (sm), 16px (base), 18px (lg), 24px (xl), 32px (2xl)
- Weights: 400 (regular), 500 (medium), 600 (semibold)

### Design Principles
- No gradients
- No emojis
- Borders: 1px solid, rounded-md (6px)
- Spacing: 4px grid system
- Transitions: 150ms ease-out (only opacity and transform)
- Icons: Bootstrap Icons only, 16px/20px sizes
- Cards: subtle border, no shadow (light), slight border (dark)

---

## Verification Plan

### Automated Tests
- Backend: `pytest` for all service modules, API endpoints
- Frontend: Verify build succeeds with `npm run build`
- Tauri: `cargo build` verification for the desktop wrapper

### Manual Verification
1. Launch application via `python launch.py`
2. Complete onboarding flow end-to-end
3. Create a job application, verify CV + cover letter generation
4. Verify dashboard displays correct stats
5. Test dark/light theme toggle
6. Test interview preparation flow

### Browser Testing
- Launch the dev server and visually verify all pages via the browser tool
- Test responsive layouts at standard desktop sizes
- Verify smooth transitions and loading states

---

## Phased Execution Order

| Phase | Description | Dependencies |
|-------|-------------|--------------|
| **1** | Project scaffolding, Tauri setup, design system, backend restructuring | Rust installation |
| **2** | Database, user profile, onboarding flow | Phase 1 |
| **3** | LLM interface, embedding system, RAG pipeline | Phase 2 |
| **4** | LaTeX templates, PDF generation | Phase 3 |
| **5** | Job application workflow, scoring, dashboard | Phase 3, 4 |
| **6** | Interview preparation module | Phase 3, 5 |

Each phase will be documented in `docs/` as completed, and progress tracked in `task.md`.

This implementation plan is also stored in `docs/implementation_plan.md` for reference.

---

### Phase 7: Job‑Match Scenario & LaTeX Document Generation

Extends the RAG‑enabled LLM layer with a fourth scenario that evaluates a job offer against the candidate's stored CV/cover‑letter context, produces a **multi‑dimensional match report**, generates LaTeX PDFs, and persists all artefacts in SQLite.

#### Design Decisions (Confirmed)

| Decision | Choice |
|---|---|
| Scoring algorithm | Embedding-assisted **checklist** – per-dimension cosine similarity + rule-based weight aggregation |
| Score dimensions | `job_match`, `skill_match`, `education_match`, `experience_match`, `objective_match` |
| LaTeX templates | Create minimal `.tex` templates from scratch |
| PDF re-render trigger | "Re-generate" button after user edits LaTeX source |
| Progress reporting | Simple boolean `processing` flag + client polling (`GET /jobs/{id}/status` every 2 s) |
| PDF editing | Lightweight: user edits raw LaTeX source in textarea; re-renders on demand |
| DB approach | Extend existing `job_applications` table with new columns |
| Endpoint naming | `POST /jobs/evaluate`, `GET /jobs/{job_id}/download` |

#### Match-Scoring Architecture

```
Job Description
    │
    ├─► ChecklistExtractor (rule-based NLP + optional LLM)
    │        └─► JobChecklist { required_skills, preferred_skills,
    │                           education_level, education_field,
    │                           min_experience_years, objectives }
    │
    ├─► embed(job_description)   ← SentenceTransformer
    │
    └─► compare against CV sections (embedded + parsed)
              │
              ▼
         MatchScorer {
           job_match        (overall semantic cosine)     weight: 0.20
           skill_match      (checklist ∩ candidate)       weight: 0.30
           education_match  (degree level + field)        weight: 0.15
           experience_match (years + domain overlap)      weight: 0.20
           objective_match  (career goal alignment)       weight: 0.15
         }
              └─► overall_score = Σ (dimension × weight)  →  0–100 %
```

#### Proposed Changes

##### [MODIFY] [job_application.py](file:///c:/Users/Amine/Desktop/Apply/Apply-Agent/src/backend/models/job_application.py)
Add columns: `workflow_status` (pending/accepted/rejected), `cv_latex`, `cover_letter_latex`, `cv_pdf_path`, `cover_letter_pdf_path`, `processing` (bool), `dimension_scores` (JSON).

##### [NEW] [job_schemas.py](file:///c:/Users/Amine/Desktop/Apply/Apply-Agent/src/backend/schemas/job_schemas.py)
Pydantic schemas: `JobOfferIn`, `DimensionScores`, `JobEvaluationOut`.

##### [NEW] [checklist_extractor.py](file:///c:/Users/Amine/Desktop/Apply/Apply-Agent/src/backend/AI/llm/checklist_extractor.py)
Rule-based + LLM-assisted extraction of `JobChecklist` from a job description.

##### [NEW] [match_scorer.py](file:///c:/Users/Amine/Desktop/Apply/Apply-Agent/src/backend/AI/llm/match_scorer.py)
Pure deterministic scorer: `score()`, `_cosine()`, `_skill_overlap()`, `_education_score()`, `_experience_score()`, `_objective_score()`, `overall()`.

##### [NEW] [job_match_service.py](file:///c:/Users/Amine/Desktop/Apply/Apply-Agent/src/backend/AI/llm/job_match_service.py)
Async orchestrator: `evaluate_job()` → extract → embed → score → persist → enqueue PDF generation. `generate_documents()` background task. `update_workflow_status()`.

##### [MODIFY] [rag_service.py](file:///c:/Users/Amine/Desktop/Apply/Apply-Agent/src/backend/AI/llm/rag_service.py)
Add `evaluate_job(job_data, session_id)` delegator method (all existing methods untouched).

##### [NEW] [latex_renderer.py](file:///c:/Users/Amine/Desktop/Apply/Apply-Agent/src/backend/utils/latex_renderer.py)
`LatexRenderer.render(latex_source, job_id, doc_type) -> Path`. Runs `pdflatex` via subprocess with timeout. Raises `LatexRenderError` on failure.

##### [NEW] latex_templates/cv_template.tex + cover_letter_template.tex
Minimal professional LaTeX templates with placeholder macros.

##### [NEW] [job_router.py](file:///c:/Users/Amine/Desktop/Apply/Apply-Agent/src/backend/api/job_router.py)
6 endpoints: `POST /jobs/evaluate`, `GET /{id}/status`, `GET /{id}/download`, `PATCH /{id}/status`, `PATCH /{id}/latex`, `POST /{id}/regenerate`.

##### [MODIFY] [main.py](file:///c:/Users/Amine/Desktop/Apply/Apply-Agent/src/backend/main.py)
Register `job_router`.

##### [MODIFY] [config.py](file:///c:/Users/Amine/Desktop/Apply/Apply-Agent/src/backend/config.py)
Add `latex_output_dir`, `max_job_history`, `pdflatex_timeout_seconds`.

#### Tests (Phase 7 – ≥ 90 % coverage target)

- `test_checklist_extractor.py` – happy-path, empty input, special characters
- `test_match_scorer.py` – perfect match, zero overlap, per-dimension, weight-sum regression
- `test_job_match_service.py` – mock embeddings + LLM + DB; assert score persistence, background task, status transitions
- `test_latex_renderer.py` – mock subprocess success/failure/timeout
- `test_job_router.py` – all 6 endpoints, success + error paths

