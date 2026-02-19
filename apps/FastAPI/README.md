# FastAPI — Testing

## Setup

Install dependencies from the `apps/FastAPI/` directory:

```bash
pip install -r requirements.txt
```

## Running tests

All commands should be run from `apps/FastAPI/`.

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
