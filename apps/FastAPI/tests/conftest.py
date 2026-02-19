"""
Shared pytest fixtures and configuration.

All test data in this project is entirely synthetic and contains
no real patient information or Protected Health Information (PHI).
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# ── Path setup ────────────────────────────────────────────────────────────────
# apps/FastAPI/ is the pytest rootdir and is already on sys.path.
# We also need SyntrilloClinic/sources/ for syntrillo.* imports.

_SOURCES_PATH = Path(__file__).resolve().parents[3] / "sources"
if str(_SOURCES_PATH) not in sys.path:
    sys.path.insert(0, str(_SOURCES_PATH))

# ── Imports (after path setup) ────────────────────────────────────────────────

from fastapi.testclient import TestClient

from tests.synthetic.blood_pressure import (
    SYNTHETIC_INTERNAL_KEY,
    SYNTHETIC_PSEUDONYMS,
    make_bp_dataframe,
    make_bp_dataframe_improving,
    make_bp_dataframe_short,
    make_bp_dataframe_with_extremes,
)


# ── Synthetic DataFrame fixtures ──────────────────────────────────────────────

@pytest.fixture(scope="session")
def synthetic_bpm_df():
    """Standard 8-week, 80-reading synthetic dataset. Reused across the session."""
    return make_bp_dataframe()


@pytest.fixture(scope="session")
def synthetic_bpm_df_short():
    """Short dataset (<4 weeks) — only Current/Latest timeframe will exist."""
    return make_bp_dataframe_short()


@pytest.fixture(scope="session")
def synthetic_bpm_df_with_extremes():
    """Dataset containing injected extreme readings for extremes-filter tests."""
    return make_bp_dataframe_with_extremes()


@pytest.fixture(scope="session")
def synthetic_bpm_df_improving():
    """Dataset where SBP trends down, producing an 'improving' progress signal."""
    return make_bp_dataframe_improving()


# ── BloodPressureAnalysis fixtures ────────────────────────────────────────────

def _build_loaded_bp(bpm_df):
    """
    Instantiate BloodPressureAnalysis with SyntrilloDatabaseManager mocked out,
    inject the provided synthetic DataFrame, and pre-compute timeframes +
    aggregated metadata so analysis methods are immediately usable.
    """
    # Import here so the module-level SOURCES_PATH injection has already run
    from syntrillo.blood_pressure.analysis import BloodPressureAnalysis

    with patch("syntrillo.blood_pressure.analysis.SyntrilloDatabaseManager"):
        bp = BloodPressureAnalysis(SYNTHETIC_INTERNAL_KEY)

    bp.bpm_df = bpm_df.copy()
    bp.calculate_timeframes()
    bp.calculate_aggregated_metadata()
    return bp


@pytest.fixture(scope="session")
def loaded_bp(synthetic_bpm_df):
    """Fully loaded BloodPressureAnalysis backed by the standard synthetic dataset."""
    return _build_loaded_bp(synthetic_bpm_df)


@pytest.fixture(scope="session")
def loaded_bp_short(synthetic_bpm_df_short):
    """Fully loaded BloodPressureAnalysis backed by the short synthetic dataset."""
    return _build_loaded_bp(synthetic_bpm_df_short)


@pytest.fixture(scope="session")
def loaded_bp_with_extremes(synthetic_bpm_df_with_extremes):
    """Fully loaded BloodPressureAnalysis backed by the extremes dataset."""
    return _build_loaded_bp(synthetic_bpm_df_with_extremes)


@pytest.fixture(scope="session")
def loaded_bp_improving(synthetic_bpm_df_improving):
    """Fully loaded BloodPressureAnalysis backed by the improving dataset."""
    return _build_loaded_bp(synthetic_bpm_df_improving)


# ── FastAPI TestClient fixtures ───────────────────────────────────────────────

@pytest.fixture(scope="session")
def app():
    """FastAPI application instance (shared across the session)."""
    from main import app as fastapi_app
    return fastapi_app


@pytest.fixture
def client(app):
    """
    Bare TestClient with no dependency overrides.
    Use for auth-enforcement tests where the real dependency chain must run.
    """
    with TestClient(app) as c:
        yield c


@pytest.fixture
def authed_client(app, loaded_bp):
    """
    TestClient with all data-layer dependencies overridden using synthetic data.

    Overrides installed:
      - get_syntrillo_internal_key  → SYNTHETIC_INTERNAL_KEY (no DB call)
      - get_pseudonyms              → SYNTHETIC_PSEUDONYMS   (no DB call)
      - get_loaded_bp               → pre-built loaded_bp fixture (no DB call)

    Teardown restores the original dependency_overrides dict.
    """
    from dependencies import get_pseudonyms, get_syntrillo_internal_key
    from routes.blood_pressure import get_loaded_bp

    original_overrides = dict(app.dependency_overrides)

    app.dependency_overrides[get_syntrillo_internal_key] = lambda: SYNTHETIC_INTERNAL_KEY
    app.dependency_overrides[get_pseudonyms] = lambda: SYNTHETIC_PSEUDONYMS
    app.dependency_overrides[get_loaded_bp] = lambda: loaded_bp

    with TestClient(app) as c:
        yield c

    app.dependency_overrides = original_overrides
