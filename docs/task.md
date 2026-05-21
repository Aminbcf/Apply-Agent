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

- [ ] Add modular LLM interface layer
- [ ] Add reusable embedding and RAG services
- [ ] Refactor cover letter generation onto the new interface
- [ ] Implement FastAPI `/llm/generate` endpoint and connect to frontend UI
- [ ] Write unit tests for LLMAdapter and EmbeddingAdapter integration
- [ ] Write unit tests for onboarding data persistence and front‑end update

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
