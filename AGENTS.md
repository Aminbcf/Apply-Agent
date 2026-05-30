# AGENTS Guidance Document

## Project: Apply-Agent

**Apply-Agent** is a local-first, AI-powered desktop career assistant. It lets users upload their CV, paste job descriptions, and auto-generate tailored CVs (LaTeX moderncv → PDF) and cover letters via local or external LLM inference. It also provides RAG-based job matching (5-dimension scoring) and interview preparation.

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | React 19, TypeScript, Vite 7, Tauri 2, TailwindCSS v4, Zustand 5, React Router v7, @tanstack/react-query 5, Bootstrap Icons |
| Backend | Python 3.11, FastAPI, async SQLAlchemy + SQLite, llama-cpp-python, sentence-transformers, Pydantic v2 |
| AI | Qwen2.5-0.5B-Instruct (local GGUF LoRA) or external OpenAI-compatible API; SentenceTransformer embeddings (all-MiniLM-L6-v2) |
| PDF | LaTeX via MiKTeX (pdflatex dual-pass compilation) |
| Desktop | Tauri 2 (Rust wrapper) |

## Directory Map

```
Apply-Agent/
├── launch.py                    # Launcher: starts FastAPI + Vite dev server
├── src/
│   ├── backend/
│   │   ├── main.py              # FastAPI app entry, CORS, router registration
│   │   ├── config.py            # Pydantic Settings from .env
│   │   ├── database.py          # Async SQLAlchemy engine + session factory
│   │   ├── model_registry.py    # Singleton: LLMAdapter, EmbeddingAdapter, DomainManager
│   │   ├── models/              # SQLAlchemy ORM (job_application, user_profile, user_profile_version)
│   │   ├── schemas/             # Pydantic request/response schemas
│   │   ├── routers/             # cv, onboarding, profile, dashboard
│   │   ├── api/                 # job_router, stream_router, settings_router, interview_router
│   │   ├── services/            # profile_service
│   │   ├── AI/llm/              # LLM adapters, batch generator, RAG, prompts (14 files)
│   │   ├── AI/CV-Examples/      # Few-shot CV style references
│   │   ├── AI/Cover-letter-Examples/
│   │   ├── utils/               # LatexRenderer, latex_templates/
│   │   ├── .coveragerc          # Coverage config (omits tests, demo scripts)
│   │   ├── .bandit              # Bandit security config (INI format)
│   │   └── tests/               # 14 test files
│   └── frontend/
│       └── src/
│           ├── App.tsx          # React Router setup
│           ├── components/common/  # Button, Card, Input, Badge
│           ├── components/Layout/  # AppShell, Sidebar, Header
│           ├── pages/           # Dashboard, Onboarding, Applications, Interviews, Settings
│           ├── services/api.ts  # Typed API client + SSE hook
│           ├── styles/globals.css
│           └── __tests__/       # 11 test files
├── data/                        # SQLite DB file (apply_agent.db)
├── docs/
│   ├── rules.md                 # Comprehensive AI agent coding rules (24 sections, 150 lines)
│   ├── architecture.md          # System architecture overview
│   ├── execution.md             # Local launch & validation pipeline
│   ├── implementation_plan.md   # 7-phase phased plan
│   ├── memory.md                # Aggregated cross-session memory (53 lines)
│   ├── restructure-plan.md      # SSE streaming, markdown editing architecture
│   ├── task.md                  # Task tracking
│   └── skills/coding-standards/SKILL.md  # Code quality enforcement (>=80% coverage)
├── logs/                        # Per-session logs (session_<timestamp>.md)
├── scripts/                     # export_to_gguf.py, init_local_db.py
├── .env.example                 # All environment variables documented (36 lines)
├── .github/workflows/ci.yml     # CI: Gitleaks + SonarQube + linting + tests
├── sonar-project.properties     # SonarQube Cloud config
├── run_tests.py / run_tests.ps1 # Test runners
├── issue_body.md                # Known bug descriptions
├── Workflow.md                  # Original specification document
└── README.md                    # Project README
```

## Entry Points for LLM Agents

- **Always start** by reading these documentation files in order:
  1. `docs/rules.md` – Coding guidelines, architecture principles, and **Session Memory & Persistent Logs** (section 12)
  2. `docs/memory.md` – Aggregated important insights from previous sessions
  3. `docs/skills/coding-standards/SKILL.md` – Code quality enforcement (>=80% coverage, <=3% duplication)
  4. `docs/architecture.md` – System architecture reference
  5. `docs/execution.md` – Local launch and validation pipeline
  6. `docs/task.md` – Current task tracking status
- The **primary location** for operations is the project root directory (`<project_root>`).
- Agents should also consult `Workflow.md` for the original product specification.

## How Agents Should Use the Documentation

1. **Load Rules** — Read `docs/rules.md` at session start, especially section 12 (Session Memory & Persistent Logs).
2. **Persist Knowledge** — After each logical step, append an entry to the active session log in `logs/session_<id>.md`. At session end, merge **important** entries (marked with `**Important:**`) into `docs/memory.md`.
3. **Reference Guidelines** — Before generating code, consult the **Review Checklist** in `docs/rules.md` (section 11) to ensure compliance with style, testing, security, and logging standards.
4. **Check Known Issues** — Review `issue_body.md` for open bugs. Ensure your work does not conflict with or duplicate these fixes.
5. **Verify Changes** — Run both backend and frontend tests before finalizing any work (see "Running Tests" below).

## Session Logging Protocol

Since `init_session_log()` and `finalize_session()` have not yet been implemented as Python helpers, follow this manual protocol:

1. **Create log file**: At session start, create `logs/session_<YYYYMMDD_HHMMSS>.md`.
2. **Log entries**: Append under `## <YYYY-MM-DD HH:MM>` headings. Each entry should include the action, file paths changed, rationale, and any important insights.
3. **Mark important entries**: Prefix crucial learnings with `**Important:**` so they can be identified for merging.
4. **End of session**: Review the log, copy important entries into `docs/memory.md` under the appropriate category heading, with a source reference (session ID).

> **NOTE**: Never overwrite existing logs or memory entries. Use append-only operations unless cleanup is explicitly required.

## Running Tests

### Backend
```powershell
cd src/backend
pytest --cov=. --cov-config=.coveragerc --cov-report=term-missing
```

### Frontend
```powershell
cd src/frontend
npm run test
# With coverage:
npx vitest run --coverage
```

### All Tests (from root)
```powershell
python run_tests.py     # Python helper
./run_tests.ps1         # PowerShell helper
```

## Environment Setup

- Copy `.env.example` to `.env` and fill in values.
- Python venv (at repo root): `.venv\Scripts\Activate.ps1`
- Backend deps: `pip install -r src/backend/requirements.txt`
- Frontend deps: `cd src/frontend && npm install`
- Node.js: v20+
- LaTeX: MiKTeX with `pdflatex` on PATH
- Rust/Cargo: required for Tauri builds (rustc 1.95.0 confirmed)

## Known Issues

1. **CV Not Generating (Local Model):** `batch_generator.py` uses `ThreadPoolExecutor` for parallel section generation when CPU cores > 4. Local `LlamaCppAdapter` holds a global lock in llama.cpp, causing thread contention and timeouts. The frontend receives no output.
   - Proposed fix: add `_can_run_parallel` check in `batch_generator.py` returning `False` when provider is local `LlamaCppAdapter`, forcing sequential execution.

2. **Cover Letter Hallucinations:** The fine-tuned local model outputs training artifacts — repeated `[[[Generated Cover Letter]]]` and `[[source: role]]` markers — because `create_completion` in `LlamaCppAdapter` lacks stop tokens for these patterns.
   - Proposed fix: add `stop=["[[[", "[[source:", "<|im_end|>"]` to all `LlamaCppAdapter.create_completion` calls.

Full details in `issue_body.md`.

## Checklist for LLM Agents

| Item | Description |
|------|-------------|
| **Load Docs** | Read `docs/rules.md`, `docs/memory.md`, `docs/skills/coding-standards/SKILL.md` at session start |
| **Maintain Log** | Record every action in `logs/session_<id>.md` |
| **Persist Memory** | Merge critical insights into `docs/memory.md` at session end |
| **Check Known Issues** | Review `issue_body.md`; don't conflict with open bugs |
| **Follow Guidelines** | Verify output against checklists in `docs/rules.md` sections 11 & 12 |
| **Run Tests** | Ensure `pytest` (backend) and `npm run test` (frontend) pass before finalizing |
| **No Secrets** | Never hard-code paths, keys, or host-specific data; use `.env` and placeholders |
| **Code Quality** | Maintain >=80% test coverage, <=3% duplication, zero critical SonarQube issues |
| **Append Only** | Never overwrite logs or memory — use append-only operations |

---

*This file is the primary entry point for LLM agents. Keep it updated as the project evolves.*
