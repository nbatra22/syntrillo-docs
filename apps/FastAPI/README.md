# FastAPI

All commands should be run from `apps/FastAPI/`.

## Setup

**1. Install dependencies**

```bash
pip install -r requirements.txt
```

**2. Create the syntrillo symlink** (one-time, required for DB connections)

```bash
ln -s ../../sources/syntrillo syntrillo
```

This makes `syntrillo` importable and resolves the relative SSL certificate path used by the database connection layer.

**3. Configure environment variables**

Copy or create a `.env` file in `apps/FastAPI/` with the following keys:

```
FAST_ENV=development          # set to "production" in prod
DATABASE_SERVER=AWS           # or PythonAnywhere
CORS_ORIGINS=["http://localhost:5173"]
```

Add your database credentials and any other secrets as needed (see the existing `.env` for reference — never commit it).

## Starting the server

```bash
# Development — auto-reload on file changes
uvicorn main:app --reload

# Specify host/port if needed
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The server starts at `http://127.0.0.1:8000` by default.

Interactive API docs are available at:
- `http://127.0.0.1:8000/docs` — Swagger UI
- `http://127.0.0.1:8000/redoc` — ReDoc
- `http://127.0.0.1:8000/health` — health check endpoint

## Running tests

```bash
# Run all tests
pytest

# Unit tests only (no HTTP layer, no network)
pytest tests/unit/

# Integration tests only (HTTP layer, mocked dependencies)
pytest tests/integration/

# With coverage report
pytest --cov=. --cov-report=term-missing

# Stop on first failure
pytest -x

# Run a specific test file
pytest tests/unit/test_bp_analysis.py

# Run a specific test class or test
pytest tests/unit/test_bp_analysis.py::TestGradeMetric
pytest tests/unit/test_bp_analysis.py::TestGradeMetric::test_avg_sbp_optimal
```

## Important notes

- All test data is entirely synthetic and contains **no real patient information or PHI**.
- Auth enforcement tests (`TestAuthEnforcement`) must always pass — they verify that
  unauthenticated requests are rejected before any patient data is accessed.
- Do not add real patient identifiers, lookup codes, or health records to any file
  under `tests/`.
