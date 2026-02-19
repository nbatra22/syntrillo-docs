"""
Integration tests for the blood pressure API routes.

Uses FastAPI's TestClient (backed by httpx) to exercise the full HTTP layer,
including request validation, dependency injection, response schema shape,
and auth enforcement.

All data is entirely synthetic and contains no PHI.
Auth enforcement tests are explicitly marked to satisfy HIPAA access-control
auditability requirements.
"""

from unittest.mock import patch

import pytest
from fastapi import HTTPException, status
from fastapi.testclient import TestClient

from tests.synthetic.blood_pressure import (
    SYNTHETIC_INTERNAL_KEY,
    SYNTHETIC_PSEUDONYMS,
)

BASE = "/api/v1/blood-pressure"


# ── Health check ──────────────────────────────────────────────────────────────

def test_health_check(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


# ── Auth enforcement (HIPAA: access control must be demonstrably tested) ──────

class TestAuthEnforcement:
    """
    These tests verify that unauthenticated / unauthorised requests are
    rejected before any patient data is accessed.

    HIPAA §164.312(a)(1) — Access Control: implement technical policies and
    procedures that allow access only to authorised persons.
    """

    def test_missing_lookup_code_returns_422(self, client):
        """
        FastAPI must reject requests that omit the required temporary_lookup_code
        query parameter with a 422 Unprocessable Entity before any business
        logic runs.
        """
        resp = client.get(f"{BASE}/summary")
        assert resp.status_code == 422

    def test_invalid_lookup_code_returns_403(self, client, app):
        """
        When TemporaryLookUpCodesManagement cannot find a matching record for
        the supplied code, the dependency must return 403 Forbidden.
        No patient data is accessed.
        """
        with patch(
            "syntrillo.pseudonyms_management.temporary_lookup_codes_management"
            ".TemporaryLookUpCodesManagement.retrieve_syntrillo_internal_key",
            return_value=None,
        ):
            resp = client.get(f"{BASE}/summary?temporary_lookup_code=invalid-code")
        assert resp.status_code == 403

    def test_analysis_requires_auth(self, client):
        resp = client.get(f"{BASE}/analysis")
        assert resp.status_code == 422

    def test_extremes_requires_auth(self, client):
        resp = client.get(f"{BASE}/extremes")
        assert resp.status_code == 422

    def test_distribution_requires_auth(self, client):
        resp = client.get(f"{BASE}/distribution")
        assert resp.status_code == 422


# ── Happy-path status codes ───────────────────────────────────────────────────

class TestHappyPathStatus:
    """All data-layer dependencies overridden with synthetic data."""

    def test_summary_returns_200(self, authed_client):
        resp = authed_client.get(f"{BASE}/summary?temporary_lookup_code=test")
        assert resp.status_code == 200

    def test_analysis_returns_200(self, authed_client):
        resp = authed_client.get(f"{BASE}/analysis?temporary_lookup_code=test")
        assert resp.status_code == 200

    def test_extremes_returns_200(self, authed_client):
        resp = authed_client.get(f"{BASE}/extremes?temporary_lookup_code=test")
        assert resp.status_code == 200

    def test_distribution_returns_200(self, authed_client):
        resp = authed_client.get(f"{BASE}/distribution?temporary_lookup_code=test")
        assert resp.status_code == 200


# ── Response schema shape ─────────────────────────────────────────────────────

class TestSummarySchema:

    def test_top_level_keys(self, authed_client):
        data = authed_client.get(f"{BASE}/summary?temporary_lookup_code=test").json()
        for key in ("status", "avg_sbp", "avg_dbp", "peak_sbp", "low_sbp",
                    "symptomatic_hypotension", "near_hypotensive"):
            assert key in data, f"Missing key: {key}"

    def test_graded_metric_fields(self, authed_client):
        data = authed_client.get(f"{BASE}/summary?temporary_lookup_code=test").json()
        for key in ("avg_sbp", "avg_dbp", "peak_sbp", "low_sbp"):
            metric = data[key]
            assert "value" in metric
            assert "grade" in metric
            assert isinstance(metric["grade"], int)
            assert 0 <= metric["grade"] <= 3, f"{key}.grade out of range: {metric['grade']}"


class TestAnalysisSchema:

    def test_top_level_keys(self, authed_client):
        data = authed_client.get(f"{BASE}/analysis?temporary_lookup_code=test").json()
        assert "timeframes" in data
        assert "rows" in data
        assert "overall_progress" in data

    def test_timeframes_non_empty(self, authed_client):
        data = authed_client.get(f"{BASE}/analysis?temporary_lookup_code=test").json()
        assert len(data["timeframes"]) >= 1
        for tf in data["timeframes"]:
            assert "name" in tf
            assert "date_range" in tf

    def test_rows_non_empty(self, authed_client):
        data = authed_client.get(f"{BASE}/analysis?temporary_lookup_code=test").json()
        assert len(data["rows"]) >= 1

    def test_row_structure(self, authed_client):
        rows = authed_client.get(f"{BASE}/analysis?temporary_lookup_code=test").json()["rows"]
        for row in rows:
            assert "metric" in row
            assert "values" in row
            assert "progress" in row
            assert isinstance(row["values"], dict)

    def test_overall_progress_keys(self, authed_client):
        op = authed_client.get(f"{BASE}/analysis?temporary_lookup_code=test").json()["overall_progress"]
        # At least one of these should be present given an 8-week dataset
        assert "since_baseline" in op or "since_prior" in op


class TestExtremesSchema:

    def test_measurements_is_list(self, authed_client):
        data = authed_client.get(f"{BASE}/extremes?temporary_lookup_code=test").json()
        assert "measurements" in data
        assert isinstance(data["measurements"], list)

    def test_measurement_structure(self, authed_client):
        """Each item must have timestamp, systolic, diastolic."""
        measurements = authed_client.get(
            f"{BASE}/extremes?temporary_lookup_code=test"
        ).json()["measurements"]
        for m in measurements:
            assert "timestamp" in m
            assert "systolic" in m
            assert "diastolic" in m


class TestDistributionSchema:

    def test_data_is_list(self, authed_client):
        data = authed_client.get(f"{BASE}/distribution?temporary_lookup_code=test").json()
        assert "data" in data
        assert isinstance(data["data"], list)

    def test_hourly_data_point_structure(self, authed_client):
        items = authed_client.get(
            f"{BASE}/distribution?temporary_lookup_code=test"
        ).json()["data"]
        assert len(items) >= 1, "Expected at least one hourly data point"
        for item in items:
            assert "hour" in item
            assert "count" in item
            assert "systolic" in item
            assert "diastolic" in item
            assert isinstance(item["hour"], int)
            assert 0 <= item["hour"] <= 23

    def test_box_plot_stats_fields(self, authed_client):
        items = authed_client.get(
            f"{BASE}/distribution?temporary_lookup_code=test"
        ).json()["data"]
        for item in items:
            for side in ("systolic", "diastolic"):
                bp = item[side]
                for field in ("min", "q1", "median", "mean", "q3", "max", "outliers"):
                    assert field in bp, f"Missing {side}.{field}"


# ── Error handling ────────────────────────────────────────────────────────────

class TestErrorHandling:

    def test_too_short_date_range_returns_422(self, app):
        """
        When the BP data loader raises a 422 (e.g. date range too short),
        the endpoint should propagate it.
        """
        from dependencies import get_syntrillo_internal_key
        from routes.blood_pressure import get_loaded_bp

        original = dict(app.dependency_overrides)

        def _raise_422():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Report period is too short",
            )

        app.dependency_overrides[get_syntrillo_internal_key] = lambda: SYNTHETIC_INTERNAL_KEY
        app.dependency_overrides[get_loaded_bp] = _raise_422

        with TestClient(app) as c:
            resp = c.get(f"{BASE}/summary?temporary_lookup_code=test")

        app.dependency_overrides = original
        assert resp.status_code == 422

    def test_no_data_found_returns_404(self, app):
        """
        When the BP data loader raises a 404 (no readings found),
        the endpoint should propagate it.
        """
        from dependencies import get_syntrillo_internal_key
        from routes.blood_pressure import get_loaded_bp

        original = dict(app.dependency_overrides)

        def _raise_404():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No blood pressure data found.",
            )

        app.dependency_overrides[get_syntrillo_internal_key] = lambda: SYNTHETIC_INTERNAL_KEY
        app.dependency_overrides[get_loaded_bp] = _raise_404

        with TestClient(app) as c:
            resp = c.get(f"{BASE}/summary?temporary_lookup_code=test")

        app.dependency_overrides = original
        assert resp.status_code == 404
