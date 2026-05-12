#!/usr/bin/env python3
"""Launch FastAPI backend and React frontend from the repository root."""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BACKEND_DIR = ROOT / "src" / "backend"
FRONTEND_DIR = ROOT / "src" / "front"


def main() -> int:
    if not BACKEND_DIR.exists() or not FRONTEND_DIR.exists():
        print("Expected src/backend and src/front folders.", file=sys.stderr)
        return 1

    processes: list[subprocess.Popen[bytes]] = []

    print("Starting FastAPI backend on http://localhost:8000 ...")
    backend = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app", "--reload", "--host", "127.0.0.1", "--port", "8000"],
        cwd=BACKEND_DIR,
    )
    processes.append(backend)

    frontend_package_json = FRONTEND_DIR / "package.json"
    if frontend_package_json.exists():
        print("Starting React frontend on http://localhost:5173 ...")
        frontend = subprocess.Popen(["npm", "run", "dev"], cwd=FRONTEND_DIR)
        processes.append(frontend)
    else:
        print("No src/front/package.json found, backend started only.")

    try:
        while True:
            for proc in processes:
                code = proc.poll()
                if code is not None:
                    return code
            time.sleep(0.2)
    except KeyboardInterrupt:
        print("\nStopping services...")
        return 0
    finally:
        for proc in processes:
            if proc.poll() is None:
                proc.terminate()


if __name__ == "__main__":
    raise SystemExit(main())
