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


