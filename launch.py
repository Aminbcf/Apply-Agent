#!/usr/bin/env python3
"""Launch FastAPI backend and React frontend from the repository root."""

from __future__ import annotations

import subprocess
import sys
import os
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BACKEND_DIR = ROOT / "src" / "backend"
FRONTEND_DIR = ROOT / "src" / "frontend"
PROJECT_VENV_PYTHON = ROOT / ".venv" / "Scripts" / "python.exe"


def find_npm_executable() -> str | None:
    for candidate in ("npm", "npm.cmd", "npm.exe"):
        resolved = shutil.which(candidate)
        if resolved:
            return resolved

    windows_candidates = [
        Path(os.environ.get("ProgramFiles", r"C:\\Program Files")) / "nodejs" / "npm.cmd",
        Path(os.environ.get("ProgramFiles(x86)", r"C:\\Program Files (x86)")) / "nodejs" / "npm.cmd",
        Path(os.environ.get("LocalAppData", str(Path.home() / "AppData" / "Local"))) / "Programs" / "nodejs" / "npm.cmd",
    ]
    for candidate in windows_candidates:
        if candidate.exists():
            return str(candidate)

    return None


def find_backend_python() -> str:
    if PROJECT_VENV_PYTHON.exists():
        return str(PROJECT_VENV_PYTHON)
    return sys.executable


def main() -> int:
    if not BACKEND_DIR.exists() or not FRONTEND_DIR.exists():
        print("Expected src/backend and src/frontend folders.", file=sys.stderr)
        return 1

    processes: list[subprocess.Popen[bytes]] = []

    print("Starting FastAPI backend on http://localhost:8000 ...")
    backend_python = find_backend_python()
    backend = subprocess.Popen(
        [backend_python, "-m", "uvicorn", "main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"],
        cwd=BACKEND_DIR,
    )
    processes.append(backend)

    frontend_package_json = FRONTEND_DIR / "package.json"
    if frontend_package_json.exists():
        npm_executable = find_npm_executable()
        if npm_executable is None:
            print(
                "npm was not found in this shell. Start the launcher from a terminal where Node.js is on PATH, "
                "or install Node.js with the official Windows installer.",
                file=sys.stderr,
            )
        else:
            print("Starting React frontend on http://localhost:5173 ...")
            frontend = subprocess.Popen([npm_executable, "run", "dev"], cwd=FRONTEND_DIR)
            processes.append(frontend)
    else:
        print("No src/frontend/package.json found, backend started only.")

    try:
        return processes[0].wait()
    except KeyboardInterrupt:
        print("\\nStopping services...")
        return 0
    finally:
        for proc in processes:
            if proc.poll() is None:
                proc.terminate()


if __name__ == "__main__":
    raise SystemExit(main())
