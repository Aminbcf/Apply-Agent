# Project Memory

## Coding Standards
- **Bandit Configuration:** When using a `.bandit` file, it MUST be in INI format with a `[bandit]` header. List arrays (like `exclude_dirs` or `skips`) must be comma-separated strings without brackets (e.g., `exclude_dirs = .venv,tests,__pycache__`).
- **Nosec Comments:** When suppressing Bandit warnings, always explicitly write `# nosec BXXX` with the exact ID (e.g., `# nosec B603`), avoiding inline descriptive text that breaks the parser.
- **Cross-Platform fetch in Vitest:** Always reference global fetches in Vite/Vitest environments as `globalThis.fetch` instead of Node's `global.fetch` to ensure flawless TypeScript compiler checks (Session ID: phase1_20260520_111302).
- **Card and Custom Component Props:** Custom UI components must support and forward basic CSS styling props like `style?: CSSProperties` to retain standard HTML/React flexibility (Session ID: phase1_20260520_111302).
- **Interactive Component Accessibility Tests:** Always write explicit test cases for keyboard handlers on customized active HTML elements (such as `role="button"` divs) to guarantee that both mouse clicks and keyboard actions are verified and covered by testing suites (Session ID: phase1_20260520_121653).
- **FastAPI AsyncClient in Pytest Async Suites:** When using async fixtures in Pytest async suites, ensure API tests are refactored to use `httpx.AsyncClient` to avoid `pytest.PytestRemovedIn9Warning` errors on synchronous test cases (Session ID: phase1_20260520_125610).
- **Native Button for Card Interactive Components:** Rendering a native `<button type="button">` element instead of custom divs with `role="button"` for interactive components resolves all SonarQube accessibility warnings automatically (Session ID: phase1_20260520_125610).
- **Secure Mock Base URL Protocol:** Specifying `https` scheme base URLs (e.g. `https://testserver` or `https://test`) inside unit testing clients (FastAPI `TestClient` or `AsyncClient`) prevents insecure protocol alerts from triggering on local mock network calls (Session ID: phase1_20260520_125610).
- **SQLAlchemy Mutation Tracking for SQLite Nested Columns:** SQLite databases do not automatically detect mutation in JSON array or dictionary types (like `experience`, `skills`, or parsed CV structures) on standard save operations. To guarantee database transaction persistence, the ORM object must have its JSON fields explicitly declared modified using `sqlalchemy.orm.attributes.flag_modified(profile, field_name)` prior to the transaction commit (Session ID: phase2_20260520_174800).
- **FastAPI UploadFile Stream Constraints:** Reading raw stream buffers for multi-part file uploads (FastAPI `UploadFile`) should enforce maximum size limitations via chunked block reads to prevent server resource exhaustion while keeping mock unit testing fully isolated (Session ID: phase2_20260520_174800).
- **SQLAlchemy UUID Lookups in SQLite:** When fetching records by UUID from a SQLite database via SQLAlchemy, explicitly parse string identifiers into `uuid.UUID` objects before the `where()` clause. Passing string variables directly into `where(Model.id == job_id_str)` throws a `StatementError ('str' object has no attribute 'hex')` (Session ID: phase7_20260521).
- **Mocking SQLAlchemy add() in Async Tests:** In async FastAPI endpoint tests, `AsyncSession.add()` is a synchronous method while `commit()` and `refresh()` are coroutines. When mocking the database session (e.g. `mock_db = AsyncMock()`), explicitly set `mock_db.add = MagicMock()` to prevent `RuntimeWarning: coroutine was never awaited` during tests (Session ID: phase7_20260521).

## RAG, Speed & External API Architecture (Session: phase_rag_opt_20260522)

### External API Provider Design
- **Pattern:** `ExternalApiAdapter(LLMAdapter)` in `llm_interface.py` — OpenAI-compatible REST, user-configurable `base_url`, `model`, `api_key`. Factory `get_llm_adapter(settings)` returns `ExternalApiAdapter` when `settings.llm_provider == "external"`, else `QwenAdapter`.
- **Settings fields added to `config.py`:** `llm_provider`, `external_api_base_url`, `external_api_key`, `external_api_model`, `external_api_timeout`, `llm_quantize_4bit`, `llm_max_new_tokens`.
- **Hot-swap:** `model_registry.swap_llm(adapter)` allows runtime provider change via `POST /settings/llm` without restart.
- **Frontend:** Full Settings page at `/settings` — user enters Base URL + Model Name + API Key + "Test Connection" button. No predefined provider list; fully free-form.

### Local Model Optimization (4 GB VRAM GPU)
- **Quantization:** `BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_compute_dtype=torch.float16, bnb_4bit_quant_type="nf4", bnb_4bit_use_double_quant=True)`. Expected VRAM: ~1.2 GB for 1.5B param Qwen model.
- **When `llm_provider == "external"`:** Skip all local model loading at startup (startup < 1 s).
- **`max_new_tokens`:** Raised from 256 → `settings.llm_max_new_tokens` (default 1024).

### RAG Context Sources (ALL of the following)
- `UserProfile` from SQLite: name, email, phone, skills, education, experience, career_goals, raw_cv_text, projects, certifications, languages.
- `JobApplication` record: title, company, description, extracted checklist, dimension_scores.
- Past **accepted/confirmed** `JobApplication` records (up to 3 most recent) as few-shot examples: cv_text_snippet + cover_letter_snippet.
- Files from `AI/CV-Examples/` directory (markdown reference CVs).
- Files from `AI/Cover-letter-Examples/` directory (markdown reference cover letters).

### Prompt Architecture
- Prompts live in `AI/llm/prompts/{scenario}.md` and use `{cv_context_json}`, `{job_context_json}`, `{few_shot_examples_json}`, `{cv_examples}`, `{cover_letter_examples}` placeholders.
- `build_rag_prompt(scenario, cv_context, job_context, few_shot_examples, example_files)` replaces the old `build_prompt`.
- Old `build_prompt` is kept as a thin compatibility shim calling `build_rag_prompt`.

### Settings API Endpoints
- `GET /settings/llm` — returns current provider config (key is redacted, only `has_api_key: bool`).
- `POST /settings/llm` — updates config at runtime, hot-swaps adapter.
- `GET /settings/llm/test` — sends a minimal test prompt, returns `{ ok, latency_ms, model_used }`.

### File Locations Summary
- New: `src/backend/api/settings_router.py`
- New: `src/frontend/src/pages/Settings/Settings.tsx`
- Modified: `config.py`, `llm_interface.py`, `rag_service.py`, `stream_router.py`, `model_registry.py`, `main.py`, `App.tsx`, `api.ts`, `AppShell`
- Modified prompts: `AI/llm/prompts/cv.md`, `cover_letter.md`; New: `job_match.md`
- New tests: `tests/test_llm_interface.py`, `tests/test_rag_service.py`, `tests/test_settings_router.py`

