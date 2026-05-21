# Apply-Agent Task Tracker

Status snapshot for the current workspace before continuing implementation.

## Completed Before This Session

- [x] Existing AI/CV foundation is present in `src/backend/AI/`:
  - `cv_processor.py`
  - `domain_embeddings.py`
  - `raw_cv_parser.py`
  - `cover_letter_generator.py`
  - demo and test helpers
- [x] Tauri + Vite + React + TypeScript scaffold exists in `src/frontend/`
- [x] Rust/Tauri project files are present in `src/frontend/src-tauri/`
- [x] Backend still runs as the current FastAPI prototype in `src/backend/main.py`

## Completed In This Pass

- [x] Created this task tracker
- [x] Added repo ignore rules for common build and Python artifacts
- [x] Updated the launcher to point at `src/frontend`
- [x] Replaced the starter frontend screen with an app shell
- [x] Added persistent theme state and global design tokens
- [x] Added a typed frontend API client
- [x] Extracted the existing CV endpoints into a router
- [x] Added backend config and database scaffolding
- [x] Installed backend runtime support packages into `.venv`
- [x] Verified the refactored FastAPI app imports in `.venv`
- [x] Updated `launch.py` to resolve `npm` on Windows and prefer the repo `.venv`
- [x] Verified the full launcher starts backend and frontend together
- [x] Added `docs/execution.md` with the local launch and validation pipeline
- [x] Ignored the `docs/` contents for sensitive local notes and artifacts
- [x] Added a GitHub Actions CI workflow with SonarQube integration
- [x] Added a repository-level `sonar-project.properties` file
- [x] Upgraded the SonarQube GitHub Action to v6 and added host URL validation
- [x] Integrated SonarQube Cloud with GitHub repository
- [x] Added comprehensive free CI tools: ESLint, Pylint, Flake8, Bandit, Pytest, CodeQL
- [x] Added dependency vulnerability scanning (npm audit, safety)
- [x] Added frontend and backend unit test runners
- [x] Regenerated the frontend lockfile so CI can use `npm ci`
- [x] Migrated frontend linting to ESLint v9 flat config

## Next Work

### Phase 1 - Scaffold and Infrastructure

- [ ] Replace the remaining starter Tauri wrapper details with app-specific branding
- [ ] Add frontend layout and common UI primitives
- [ ] Expand the backend into service modules under `src/backend/services/`
- [ ] Add real database models under `src/backend/models/`
- [ ] Add onboarding and dashboard routers
- [ ] Add CI-focused automation scripts or workflow files if deployment is required later
- [ ] Add repository-specific SonarQube project settings or quality-gate tuning if needed

### Phase 2 - Persistence and Context

- [x] Add SQLite persistence layer
- [x] Add user profile and onboarding backend services
- [x] Add onboarding pages and stores in the frontend

### Phase 3 - LLM and Embeddings

- [/ ] Add modular LLM interface layer
- [/ ] Add reusable embedding and RAG services
- [/ ] Refactor cover letter generation onto the new interface
- [/ ] Implement FastAPI `/llm/generate` endpoint and connect to frontend UI
- [/ ] Write unit tests for LLMAdapter and EmbeddingAdapter integration
- [/ ] Write unit tests for onboarding data persistence and front‑end update

### Phase 4 - Templates and PDF

- [ ] Add LaTeX template files
- [ ] Add template rendering and PDF compilation service

### Phase 5 - Job Workflow and Dashboard

- [ ] Add job scoring modules
- [ ] Add job application backend service
- [ ] Add dashboard, history, and job workflow pages

### Phase 6 - Interview Prep

- [ ] Add interview RAG and mock interviewer services
- [ ] Add interview prep frontend pages

---

### Phase 7 - Job‑Match Scenario & LaTeX Document Generation

#### 7.1 · Foundation
- [x] Extend `JobApplication` model with `workflow_status`, `cv_latex`, `cover_letter_latex`, `cv_pdf_path`, `cover_letter_pdf_path`, `processing`, `dimension_scores` columns
- [x] Verify new columns created by `init_db()` on next startup (no Alembic needed for SQLite recreate)
- [x] Create `src/backend/schemas/job_schemas.py` with `JobOfferIn`, `DimensionScores`, `JobEvaluationOut`, `JobStatusOut`, `WorkflowStatusUpdate`, `LatexUpdate`
- [x] Add `latex_output_dir`, `max_job_history`, `pdflatex_timeout_seconds` to `config.py`

#### 7.2 · LaTeX Artefacts
- [x] Create `src/backend/utils/latex_templates/cv_template.tex` (minimal professional CV with macro placeholders)
- [x] Create `src/backend/utils/latex_templates/cover_letter_template.tex`
- [x] Create `src/backend/utils/latex_renderer.py`
  - [x] `LatexRenderer.render(latex_source, job_id, doc_type) -> Path`
  - [x] `_run_pdflatex(tex_path)` with configurable timeout
  - [x] `LatexRenderError` custom exception

#### 7.3 · Scoring Engine
- [x] Create `src/backend/AI/llm/checklist_extractor.py`
  - [x] `JobChecklist` dataclass (required_skills, preferred_skills, education_level, education_field, min_experience_years, objectives)
  - [x] `extract_checklist(job_description) -> JobChecklist` (regex + keyword rules)
  - [x] Optional LLM fallback for ambiguous items
- [x] Create `src/backend/AI/llm/match_scorer.py`
  - [x] `WEIGHTS` constant (job_match:0.20, skill_match:0.30, education_match:0.15, experience_match:0.20, objective_match:0.15)
  - [x] `score(job_checklist, cv_context, embeddings) -> DimensionScores`
  - [x] `_cosine(a, b)`, `_skill_overlap()`, `_education_score()`, `_experience_score()`, `_objective_score()`
  - [x] `overall(dimension_scores) -> float` (weighted sum → 0–100 %)

#### 7.4 · Service Layer
- [x] Create `src/backend/AI/llm/job_match_service.py`
  - [x] `evaluate_job(job_offer, session_id) -> JobEvaluationOut` (extract → embed → score → persist → enqueue)
  - [x] `generate_documents(job_id)` background task (Qwen prompt → LaTeX → pdflatex → DB update)
  - [x] `update_workflow_status(job_id, status)` (reject clears `HistoryCache`)
  - [x] `update_latex(job_id, doc_type, latex_source)` – save user edits
  - [x] `regenerate_pdf(job_id, doc_type)` – re-render background task
- [x] Add `evaluate_job(job_data, session_id)` delegator to `rag_service.py` (keep all existing methods)

#### 7.5 · API Layer
- [x] Create `src/backend/api/job_router.py`
  - [x] `POST /jobs/evaluate` → `JobEvaluationOut` (202)
  - [x] `GET /jobs/{job_id}/status` → polling (processing + pdf_urls)
  - [x] `GET /jobs/{job_id}/download?file_type=cv|cover|cv_latex|cover_latex`
  - [x] `PATCH /jobs/{job_id}/status` → accept / reject / pending
  - [x] `PATCH /jobs/{job_id}/latex` → save user-edited LaTeX
  - [x] `POST /jobs/{job_id}/regenerate` → re-render PDF from stored LaTeX (202)
- [x] Register `job_router` in `main.py`

#### 7.6 · Tests
- [x] `tests/test_checklist_extractor.py` – created (happy-path, empty input, special chars)
- [x] `tests/test_match_scorer.py` – created (perfect match, zero overlap, per-dimension, weight-sum)
- [x] `tests/test_job_match_service.py` – created (mock embeddings + LLM + DB; score persistence, background task, status transitions)
- [x] `tests/test_latex_renderer.py` – created (mock subprocess success/failure/timeout)
- [x] `tests/test_job_router.py` – created (all 6 endpoints, success + error paths)
- [x] Run `pytest src/backend/tests/ --cov` → target ≥ 90 % for new modules

#### 7.7 · Verification & Docs
- [x] Manual: POST sample job → verify 5-dimension scores returned
- [x] Manual: poll until `processing: false` → download PDF
- [x] Manual: edit LaTeX → regenerate → verify updated PDF
- [x] Manual: reject → verify session cache cleared
- [x] Manual: restart backend → verify job persists in SQLite
- [x] Update `docs/architecture.md` with new scenario and endpoint table
- [x] Append session log → merge insights into `docs/memory.md`
