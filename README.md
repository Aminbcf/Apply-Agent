# Apply-Agent

A standard **React + FastAPI (Python)** project layout.

## Structure

```text
.
├── launch.py
├── README.md
└── src/
    ├── backend/
    │   ├── main.py
    │   └── requirements.txt
    └── frontend/
        └── README.md
```

- `src/backend`: FastAPI backend code.
- `src/frontend`: React frontend code.
- `launch.py`: Root script to launch the app services.

## Run

1. **Backend dependencies:**
   Ensure you have a virtual environment active, then install dependencies:
   ```bash
   cd src/backend
   pip install -r requirements.txt
   cd ../..
   ```
2. **Frontend dependencies:**
   Install Node packages:
   ```bash
   cd src/frontend
   npm install
   cd ../..
   ```
3. **Start services** from repository root:
   ```bash
   python launch.py
   ```

The launcher starts FastAPI immediately and also starts React when `src/frontend/package.json` exists.

## Running Tests

We maintain comprehensive unit and integration tests across both backend and frontend to ensure maximum reliability (quality gate >= 80% test coverage).

### Backend Tests

Backend tests are powered by **pytest**. All external API calls (such as LLM or embeddings services) are mocked to keep the test suite fast and deterministic.

- **Run all tests (helper scripts):**
  - **Python:**
    ```bash
    python run_tests.py
    ```
  - **PowerShell:**
    ```powershell
    ./run_tests.ps1
    ```
- **Run tests manually with coverage:**
  ```bash
  cd src/backend
  pytest --cov=. --cov-config=.coveragerc --cov-report=term-missing
  ```

### Frontend Tests

Frontend tests are powered by **Vitest** and **Testing Library**.

- **Run all tests:**
  ```bash
  cd src/frontend
  npm run test
  ```
- **Run tests with coverage report:**
  ```bash
  cd src/frontend
  npx vitest run --coverage
  ```

## CI Notes

- The Safety dependency scan is temporarily disabled in CI due to policy file parsing errors on GitHub Actions. Re-enable once the Safety CLI policy handling is stable.
