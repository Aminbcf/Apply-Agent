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
    └── front/
        └── README.md
```

- `src/backend`: FastAPI backend code.
- `src/front`: React frontend code.
- `launch.py`: root script to launch the app services.

## Run

1. Backend dependencies:
   ```bash
   cd src/backend
   pip install -r requirements.txt
   cd ../..
   ```
2. (Optional) Initialize/install frontend dependencies in `src/front`.
3. Start services from repository root:
   ```bash
   python launch.py
   ```

The launcher starts FastAPI immediately and also starts React when `src/front/package.json` exists.
