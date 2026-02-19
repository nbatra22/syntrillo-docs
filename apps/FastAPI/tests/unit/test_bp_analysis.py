"""
Unit tests for BloodPressureAnalysis (sources/syntrillo/blood_pressure/analysis.py).

These tests exercise pure computation methods only — no network calls,
no database access. All data is entirely synthetic and contains no PHI.

Coverage areas:
  - _grade_metric          static grading thresholds
  - calculate_timeframe_metadata  per-timeframe aggregations
  - calculate_timeframes   time-window segmentation logic
  - get_analysis_data      structured output shape and progress direction
  - get_extremes           out-of-bounds filter
  - _box_plot_stats        (imported from routes) IQR whisker logic
"""

import sys
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest

# routes/ must be importable for _box_plot_stats
_APP_ROOT = Path(__file__).resolve().parents[2]
if str(_APP_ROOT) not in sys.path:
    sys.path.insert(0, str(_APP_ROOT))

from syntrillo.blood_pressure.analysis import BloodPressureAnalysis
from syntrillo.blood_pressure.constants import (
    AVG_DBP,
    AVG_SBP,
    DBP_SD,
    DIASTOLIC,
    ENGAGEMENT,
    HYPOTENSIVE_COUNT,
    LOW_DBP,
    LOW_SBP,
    MEASUREMENT_COUNT,
    PEAK_DBP,
    PEAK_SBP,
    SBP_COUNT_170,
    SBP_SD,
    SYSTOLIC,
    TIMESTAMP_LOCAL,
)
from routes.blood_pressure import _box_plot_stats
from tests.synthetic.blood_pressure import (
    SYNTHETIC_INTERNAL_KEY,
    make_bp_dataframe,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_bare_bp() -> BloodPressureAnalysis:
    """Instantiate BloodPressureAnalysis with SyntrilloDatabaseManager mocked."""
    with patch("syntrillo.blood_pressure.analysis.SyntrilloDatabaseManager"):
        return BloodPressureAnalysis(SYNTHETIC_INTERNAL_KEY)


# ── _grade_metric ─────────────────────────────────────────────────────────────

class TestGradeMetric:
    """Static method — no fixtures needed."""

    # Avg SBP
    def test_avg_sbp_optimal(self):
        assert BloodPressureAnalysis._grade_metric(AVG_SBP, 120.0) == 0

    def test_avg_sbp_caution(self):
        assert BloodPressureAnalysis._grade_metric(AVG_SBP, 133.0) == 1

    def test_avg_sbp_critical(self):
        assert BloodPressureAnalysis._grade_metric(AVG_SBP, 145.0) == 2

    # Avg DBP
    def test_avg_dbp_optimal(self):
        assert BloodPressureAnalysis._grade_metric(AVG_DBP, 75.0) == 0

    def test_avg_dbp_caution(self):
        assert BloodPressureAnalysis._grade_metric(AVG_DBP, 84.0) == 1

    def test_avg_dbp_critical(self):
        assert BloodPressureAnalysis._grade_metric(AVG_DBP, 92.0) == 2

    # Peak SBP threshold crossing
    def test_peak_sbp_below_threshold(self):
        assert BloodPressureAnalysis._grade_metric(PEAK_SBP, 165.0) == 0

    def test_peak_sbp_at_or_above_threshold(self):
        assert BloodPressureAnalysis._grade_metric(PEAK_SBP, 170.0) == 2

    # Ungraded metrics
    def test_measurement_count_returns_none(self):
        assert BloodPressureAnalysis._grade_metric(MEASUREMENT_COUNT, 30) is None

    def test_none_value_returns_none(self):
        assert BloodPressureAnalysis._grade_metric(AVG_SBP, None) is None


# ── calculate_timeframe_metadata ──────────────────────────────────────────────

class TestCalculateTimeframeMetadata:
    """Pure pandas computation — no external calls."""

    def test_basic_aggregations(self):
        bp = _make_bare_bp()
        df = pd.DataFrame({
            TIMESTAMP_LOCAL: pd.to_datetime(["2025-01-01", "2025-01-02", "2025-01-03"]),
            SYSTOLIC: [130.0, 140.0, 150.0],
            DIASTOLIC: [80.0, 85.0, 90.0],
        })
        meta = bp.calculate_timeframe_metadata(df, date_range="1/1/25 - 1/3/25")

        assert meta[MEASUREMENT_COUNT] == 3
        assert meta[AVG_SBP] == pytest.approx(140.0, abs=0.1)
        assert meta[AVG_DBP] == pytest.approx(85.0, abs=0.1)
        assert meta[PEAK_SBP] == pytest.approx(140.0, abs=0.2)  # mean of top-3
        assert meta[LOW_SBP]  == pytest.approx(140.0, abs=0.2)  # mean of bottom-3

    def test_hypotensive_count(self):
        bp = _make_bare_bp()
        df = pd.DataFrame({
            TIMESTAMP_LOCAL: pd.to_datetime(["2025-01-01", "2025-01-02", "2025-01-03", "2025-01-04"]),
            SYSTOLIC: [93.0, 92.0, 135.0, 140.0],
            DIASTOLIC: [60.0, 62.0, 85.0, 88.0],
        })
        meta = bp.calculate_timeframe_metadata(df)
        assert meta[HYPOTENSIVE_COUNT] == 2

    def test_sbp_count_170(self):
        bp = _make_bare_bp()
        df = pd.DataFrame({
            TIMESTAMP_LOCAL: pd.to_datetime(["2025-01-01", "2025-01-02", "2025-01-03"]),
            SYSTOLIC: [170.0, 175.0, 130.0],
            DIASTOLIC: [90.0, 95.0, 80.0],
        })
        meta = bp.calculate_timeframe_metadata(df)
        assert meta[SBP_COUNT_170] == 2


# ── calculate_timeframes ──────────────────────────────────────────────────────

class TestCalculateTimeframes:

    def test_short_dataset_has_no_baseline_or_prior(self, loaded_bp_short):
        """
        < 4 weeks of data → only Current or Latest timeframe should exist.
        Baseline requires ≥ 4 weeks; Prior requires ≥ 5 weeks.
        """
        tf = loaded_bp_short.timeframed_data
        assert "Baseline" not in tf
        assert "Prior" not in tf
        assert any(k in tf for k in ("Current", "Latest"))

    def test_full_dataset_has_all_three_timeframes(self, loaded_bp):
        """8-week dataset should produce Baseline, Prior, and Current/Latest."""
        tf = loaded_bp.timeframed_data
        assert "Baseline" in tf
        assert "Prior" in tf
        assert any(k in tf for k in ("Current", "Latest"))


# ── get_analysis_data ─────────────────────────────────────────────────────────

class TestGetAnalysisData:

    def test_return_shape(self, loaded_bp):
        data = loaded_bp.get_analysis_data()
        assert "timeframes" in data
        assert "rows" in data
        assert "overall_progress" in data
        assert len(data["timeframes"]) >= 1
        assert len(data["rows"]) >= 1

    def test_each_row_has_required_keys(self, loaded_bp):
        rows = loaded_bp.get_analysis_data()["rows"]
        for row in rows:
            assert "metric" in row
            assert "values" in row
            assert "progress" in row

    def test_improving_direction(self, loaded_bp_improving):
        """
        The improving dataset has SBP trending from ~155 (Baseline) to ~125 (Current).
        Avg SBP progress since_baseline should be 'improving'.
        """
        data = loaded_bp_improving.get_analysis_data()
        # Find the Avg SBP row
        avg_sbp_row = next(
            (r for r in data["rows"] if "Avg SBP" in r["metric"]),
            None,
        )
        assert avg_sbp_row is not None, "Avg SBP row not found in analysis data"
        since_baseline = avg_sbp_row["progress"].get("since_baseline")
        if since_baseline is not None:
            assert since_baseline["direction"] == "improving"


# ── get_extremes ──────────────────────────────────────────────────────────────

class TestGetExtremes:

    def test_returns_known_extreme_readings(self, loaded_bp_with_extremes):
        """
        The extremes dataset has three injected out-of-bounds readings:
          SBP=85 (< 90), SBP=175 (> 170), DBP=115 (> 110).
        All three should appear in the result.
        """
        extremes = loaded_bp_with_extremes.get_extremes()
        assert len(extremes) >= 3

        sbp_values = {e["systolic"] for e in extremes}
        dbp_values = {e["diastolic"] for e in extremes}
        assert 85.0 in sbp_values
        assert 175.0 in sbp_values
        assert 115.0 in dbp_values

    def test_no_extremes_returns_empty_list(self):
        """Dataset with all readings well within bounds → empty list."""
        bp = _make_bare_bp()
        # All SBP in [110, 150], all DBP in [70, 100] — no extremes
        df = make_bp_dataframe(sbp_mean=130.0, sbp_std=5.0, dbp_mean=85.0, dbp_std=5.0, seed=1)
        # Clip to ensure nothing strays into extreme territory
        df[SYSTOLIC] = df[SYSTOLIC].clip(95, 165)
        df[DIASTOLIC] = df[DIASTOLIC].clip(60, 105)
        bp.bpm_df = df
        assert bp.get_extremes() == []


# ── _box_plot_stats ───────────────────────────────────────────────────────────

class TestBoxPlotStats:
    """Tests for the private helper in routes/blood_pressure.py."""

    def test_correct_statistics(self):
        values = [100.0, 110.0, 120.0, 130.0, 140.0]
        stats = _box_plot_stats(values)
        assert stats is not None
        assert stats.median == pytest.approx(120.0, abs=0.1)
        assert stats.mean   == pytest.approx(120.0, abs=0.1)
        assert stats.q1     == pytest.approx(110.0, abs=1.0)
        assert stats.q3     == pytest.approx(130.0, abs=1.0)

    def test_outlier_excluded_from_whiskers(self):
        # 200 is a clear outlier; whisker max should be well below it
        values = [100.0, 105.0, 110.0, 115.0, 120.0, 200.0]
        stats = _box_plot_stats(values)
        assert stats is not None
        assert 200.0 in stats.outliers
        assert stats.max < 200.0

    def test_empty_list_returns_none(self):
        assert _box_plot_stats([]) is None
