"""
Pydantic schemas for the blood pressure feature.

All HTML rendering is removed — React handles presentation.
The API returns structured JSON only.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ── Shared building blocks ────────────────────────────────────────────────────

class GradedValue(BaseModel):
    """A metric value paired with a severity grade."""
    value: Optional[Any] = None
    grade: int = Field(default=0, description="0=optimal, 1=warning, 2=critical, 3=severe")


class DateRange(BaseModel):
    start: Optional[str] = None
    end: Optional[str] = None


# ── /analysis ─────────────────────────────────────────────────────────────────

class BPMeasurement(BaseModel):
    """A single extreme blood pressure reading."""
    timestamp: str
    systolic: float
    diastolic: float


class AnalysisRow(BaseModel):
    """One row of the blood pressure analysis table."""
    metric: str
    baseline: Optional[Any] = None
    prior: Optional[Any] = None
    current: Optional[Any] = None
    since_baseline: Optional[Any] = None
    since_prior: Optional[Any] = None


class SummaryStats(BaseModel):
    date_range: DateRange
    status: GradedValue
    avg_sbp: GradedValue
    avg_dbp: GradedValue
    peak_sbp: GradedValue
    low_sbp: GradedValue
    symptomatic_hypotension: GradedValue
    near_hypotensive: GradedValue


class BPAnalysisResponse(BaseModel):
    analysis: List[AnalysisRow]
    extremes: List[BPMeasurement]
    summary_stats: SummaryStats


# ── /hr ───────────────────────────────────────────────────────────────────────

class BPHRResponse(BaseModel):
    """Resting heart rate averages across timeframes."""
    average_rhr_baseline: Optional[float] = None
    average_rhr_trailing: Optional[float] = None
    average_rhr_prior: Optional[float] = None
    baseline_start_date: Optional[str] = None
    baseline_end_date: Optional[str] = None
    prior_start_date: Optional[str] = None
    prior_end_date: Optional[str] = None
    current_start_date: Optional[str] = None
    current_end_date: Optional[str] = None


# ── /metrics ──────────────────────────────────────────────────────────────────

class HRMeasurements(BaseModel):
    baseline_rhr: Optional[float] = None
    trailing_rhr: Optional[float] = None


class BPMetricsResponse(BaseModel):
    ssq_score: Optional[Any] = None
    bmi: Optional[float] = None
    hr_measurements: HRMeasurements


# ── /biometrics ───────────────────────────────────────────────────────────────

class BMIDataPoint(BaseModel):
    bmi: Optional[float] = None
    date: Optional[str] = None


class SSQData(BaseModel):
    ssq_current: Optional[Any] = None
    ssq_prior: Optional[Any] = None
    ssq_baseline: Optional[Any] = None
    ssq_baseline_date: Optional[str] = None
    ssq_prior_date: Optional[str] = None
    ssq_current_date: Optional[str] = None


class BPBiometricsResponse(BaseModel):
    # Tuples (value, date) are serialized as lists by JSON.
    # Structure mirrors legacy: {"active": {...}, "inactive": {...}}
    physical_activity_data: Dict[str, Any]
    # Structure mirrors legacy: {"bmi_baseline": ..., "bmi_prior": ..., "bmi_current": ...}
    bmi_data: Dict[str, Optional[BMIDataPoint]]
    ssq_data: SSQData