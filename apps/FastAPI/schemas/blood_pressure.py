"""
Pydantic schemas for the blood pressure feature.

Endpoint → schema mapping:
  GET /summary      → BPSummaryResponse
  GET /analysis     → BPAnalysisResponse
  GET /extremes     → BPExtremesResponse
  GET /distribution → BPDistributionResponse
  GET /hr           → BPHRResponse
  GET /biometrics   → BPBiometricsResponse
  GET /metrics      → BPMetricsResponse  (quick patient stats, no date range)
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ── Shared ────────────────────────────────────────────────────────────────────

class GradedMetric(BaseModel):
    """A single metric value with a pre-computed severity grade.

    Grade scale: 0 = optimal, 1 = caution, 2 = critical, 3 = severe.
    React maps grade → colour; no CSS is sent from the server.
    """
    value: Optional[Any] = None
    grade: int = Field(default=0, description="0=optimal 1=caution 2=critical 3=severe")


# ── GET /summary ──────────────────────────────────────────────────────────────

class BPSummaryResponse(BaseModel):
    """Key blood pressure metrics with grades for the current/latest timeframe.

    Powers the summary card at the top of the BP tab (target vs actual view).
    """
    date_range: Optional[str] = None
    status: GradedMetric
    avg_sbp: GradedMetric
    avg_dbp: GradedMetric
    peak_sbp: GradedMetric
    low_sbp: GradedMetric
    symptomatic_hypotension: GradedMetric
    near_hypotensive: GradedMetric


# ── GET /analysis ─────────────────────────────────────────────────────────────

class TimeframeInfo(BaseModel):
    """Metadata for a single analysis timeframe column."""
    name: str
    date_range: str


class MetricValue(BaseModel):
    """One cell in the analysis table: the numeric value + its grade."""
    value: Optional[float] = None
    grade: Optional[int] = Field(
        default=None,
        description="0=optimal 1=caution 2=critical. None means no colour coding for this metric.",
    )


class ProgressDelta(BaseModel):
    """Progress score for a single metric relative to a reference timeframe."""
    delta_pts: int
    direction: str = Field(description="'improving' | 'worsening' | 'same'")


class MetricProgress(BaseModel):
    """Progress deltas for a single row, relative to baseline and prior."""
    since_baseline: Optional[ProgressDelta] = None
    since_prior: Optional[ProgressDelta] = None


class AnalysisRow(BaseModel):
    """One row of the analysis table."""
    metric: str
    values: Dict[str, MetricValue]  # keyed by timeframe name, e.g. "Baseline"
    progress: MetricProgress


class OverallProgress(BaseModel):
    """Aggregate point-based progress across all tracked metrics."""
    since_baseline: Optional[ProgressDelta] = None
    since_prior: Optional[ProgressDelta] = None


class BPAnalysisResponse(BaseModel):
    """Full timeframed analysis table.

    Powers the detailed metrics table below the summary card.
    """
    timeframes: List[TimeframeInfo]
    rows: List[AnalysisRow]
    overall_progress: OverallProgress


# ── GET /extremes ─────────────────────────────────────────────────────────────

class BPMeasurement(BaseModel):
    """A single blood pressure reading."""
    timestamp: str
    systolic: float
    diastolic: float


class BPExtremesResponse(BaseModel):
    """Out-of-bounds measurements: SBP < 90, SBP > 170, or DBP > 110."""
    measurements: List[BPMeasurement]


# ── GET /distribution ─────────────────────────────────────────────────────────

class BoxPlotStats(BaseModel):
    """Box-and-whisker statistics for one group (hour + measurement type).

    Whiskers use the 1.5×IQR rule; values beyond are listed as outliers.
    """
    min: float
    q1: float
    median: float
    mean: float
    q3: float
    max: float
    outliers: List[float]


class HourlyDataPoint(BaseModel):
    """Systolic and diastolic box plot stats for one hour of the day (0–23)."""
    hour: int
    count: int
    systolic: BoxPlotStats
    diastolic: BoxPlotStats


class BPDistributionResponse(BaseModel):
    """Measurement spread by hour of day.

    Powers the distribution chart showing when readings tend to be
    highest/lowest and how variable they are throughout the day.
    """
    data: List[HourlyDataPoint]


# ── GET /hr ───────────────────────────────────────────────────────────────────

class BPHRResponse(BaseModel):
    """Resting heart rate averages across baseline, prior, and current timeframes."""
    average_rhr_baseline: Optional[float] = None
    average_rhr_trailing: Optional[float] = None
    average_rhr_prior: Optional[float] = None
    baseline_start_date: Optional[str] = None
    baseline_end_date: Optional[str] = None
    prior_start_date: Optional[str] = None
    prior_end_date: Optional[str] = None
    current_start_date: Optional[str] = None
    current_end_date: Optional[str] = None


# ── GET /biometrics ───────────────────────────────────────────────────────────

class BMIDataPoint(BaseModel):
    bmi: Optional[float] = None
    date: Optional[str] = None


class SSQData(BaseModel):
    """Salt sensitivity questionnaire scores across timeframes."""
    ssq_current: Optional[Any] = None
    ssq_prior: Optional[Any] = None
    ssq_baseline: Optional[Any] = None
    ssq_baseline_date: Optional[str] = None
    ssq_prior_date: Optional[str] = None
    ssq_current_date: Optional[str] = None


class BPBiometricsResponse(BaseModel):
    """Contextual biometric data: physical activity, BMI history, SSQ scores."""
    physical_activity_data: Dict[str, Any]
    bmi_data: Dict[str, Optional[BMIDataPoint]]
    ssq_data: SSQData


# ── GET /metrics ──────────────────────────────────────────────────────────────

class HRMeasurements(BaseModel):
    baseline_rhr: Optional[float] = None
    trailing_rhr: Optional[float] = None


class BPMetricsResponse(BaseModel):
    """Quick scalar metrics for the patient — no date-range dependency."""
    ssq_score: Optional[Any] = None
    bmi: Optional[float] = None
    hr_measurements: HRMeasurements