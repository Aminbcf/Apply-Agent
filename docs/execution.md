# Apply-Agent Execution Guide

This document records the practical pipeline used to start, validate, and keep the project runnable on Windows.

## Runtime Layout

- Backend: Python FastAPI in `src/backend`
- Frontend: React + Vite in `src/frontend`
- Launcher: `launch.py` at the repository root
- Primary Python environment: repo `.venv`
- Frontend package manager: `npm`

## Local Launch Pipeline

1. Activate the project environment.

```powershell
Set-Location C:/Users/Amine/Desktop/Apply/Apply-Agent
.\.venv\Scripts\Activate.ps1
```

2. Start the full stack from the repository root.

```powershell
python launch.py
```

What this does:

- Starts FastAPI with the project `.venv` Python.
- Starts the frontend with `npm run dev`.
- Keeps both processes attached to the same terminal session.

3. Open the services if you want to verify them manually.

- Backend health and API routes: `http://localhost:8000`
- Frontend dev server: `http://localhost:1420` or the port shown by Vite

## CI/CD Style Validation Pipeline

This is the lightweight validation sequence currently used to keep the project healthy.

### Stage 1: Environment Check

- Confirm the repo `.venv` exists.
- Confirm `npm` is available on PATH.
- Confirm the launcher can resolve the project Python and Node executables.

### Stage 2: Backend Validation

```powershell
Set-Location C:/Users/Amine/Desktop/Apply/Apply-Agent/src/backend
C:/Users/Amine/Desktop/Apply/Apply-Agent/.venv/Scripts/python.exe -c "import main; print(main.app.title)"
```

Expected result:

- `Apply-Agent API`

### Stage 3: Frontend Validation

```powershell
Set-Location C:/Users/Amine/Desktop/Apply/Apply-Agent/src/frontend
npm run build
```

Expected result:

- Vite completes a production build without errors.

### Stage 4: End-to-End Launch

```powershell
Set-Location C:/Users/Amine/Desktop/Apply/Apply-Agent
python launch.py
```

Expected result:

- FastAPI starts with the project `.venv` Python.
- Vite starts from `src/frontend`.
- No `FileNotFoundError` for `npm`.
- No import error for `uvicorn` or `pydantic_settings`.

## Operational Notes

- If `npm` is installed but not found, start the shell from a terminal where Node.js is already on PATH.
- If the backend imports fail, run the launcher with the repo `.venv` or reinstall backend dependencies there.
- If Vite uses a different port, trust the terminal output printed by `npm run dev`.

## Current Known Good Commands

```powershell
Set-Location C:/Users/Amine/Desktop/Apply/Apply-Agent
python launch.py
```

```powershell
Set-Location C:/Users/Amine/Desktop/Apply/Apply-Agent/src/frontend
npm run build
```

```powershell
Set-Location C:/Users/Amine/Desktop/Apply/Apply-Agent/src/backend
C:/Users/Amine/Desktop/Apply/Apply-Agent/.venv/Scripts/python.exe -c "import main; print(main.app.title)"
```