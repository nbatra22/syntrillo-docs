"""
Blood pressure routes — FastAPI port of the legacy Flask blueprint.

Legacy route → new endpoint mapping:
  POST /healthie/iframe_provider_tab/blood_pressure/analysis   → GET /api/v1/blood-pressure/summary
                                                                 GET /api/v1/blood-pressure/analysis
                                                                 GET /api/v1/blood-pressure/extremes
                                                                 GET /api/v1/blood-pressure/distribution
  GET  /healthie/iframe_provider_tab/blood_pressure/download   → GET /api/v1/blood-pressure/download
  POST /healthie/iframe_provider_tab/blood_pressure/metrics    → GET /api/v1/blood-pressure/metrics
  POST /healthie/iframe_provider_tab/blood_pressure/hr         → GET /api/v1/blood-pressure/hr
  POST /healthie/iframe_provider_tab/blood_pressure/biometrics → GET /api/v1/blood-pressure/biometrics

Key differences from the legacy implementation:
  - No HTML is returned; React handles all rendering.
  - The single /analysis endpoint is split into focused sub-endpoints that
    the React frontend can fetch independently or in parallel.
  - A shared `get_loaded_bp` dependency instantiates BloodPressureAnalysis
    and loads the patient's data once per request.
  - PDF download uses the legacy BloodPressureAnalysis (aliased as
    LegacyBPAnalysis) because BloodPressureReport requires DataFrames.
  - PDF analysis is computed server-side; the client no longer sends
    pre-rendered JSON (unlike the legacy download endpoint).
  - All endpoints accept temporary_lookup_code as a query parameter so
    FastAPI's dependency injection can cache identity resolution within
    a single request.
"""

import secrets
import string
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse

SOURCES_PATH = Path(__file__).resolve().parents[3] / "sources"
sys.path.insert(0, str(SOURCES_PATH))

from syntrillo.api_healthie.constants import RHR_CATEGORY, WEIGHT_CATEGORY
from syntrillo.api_healthie.forms import HealthieForms
from syntrillo.api_healthie.user import HealthieUser
from syntrillo.api_healthie.utils import HealthieUtils
from syntrillo.blood_pressure.analysis import BloodPressureAnalysis
from syntrillo.blood_pressure.constants import DIASTOLIC, SYSTOLIC, TIMESTAMP_LOCAL
from syntrillo.bp_analysis.bp_analysis import BloodPressureAnalysis as LegacyBPAnalysis
from syntrillo.bp_analysis.bp_report import BloodPressureReport
from syntrillo.remote_monitoring.syntrillo_database_manager import SyntrilloDatabaseManager
from syntrillo.stroke_risk_score_v2.agg_data import (
    calc_rhr_metadata,
    get_healthie_metric_data,
    get_srs_healthie_data,
)
from syntrillo.stroke_risk_score_v2.utils import calculate_bmi, get_biometric_data, get_patient_info
from syntrillo.system.local_environment_and_secrets import LocalEnvironmentAndSecrets
from syntrillo.system.logger import logger

from dependencies import get_pseudonyms, get_syntrillo_internal_key
from schemas.blood_pressure import (
    BPAnalysisResponse,
    BPBiometricsResponse,
    BPDistributionResponse,
    BPExtremesResponse,
    BPHRResponse,
    BPMetricsResponse,
    BPSummaryResponse,
    BoxPlotStats,
    GradedMetric,
    HourlyDataPoint,
    HRMeasurements,
    SSQData,
)

router = APIRouter()

# Rows suppressed only in the legacy PDF download (not in API responses)
_ROWS_TO_REMOVE = {"SBP CV (%)", "DBP CV (%)", "SBP Count (>= 175)"}
_ROW_RENAME = {"Hypotensive Count⁴": "Near-Hypotensive Events⁴"}


# ── Shared dependency ─────────────────────────────────────────────────────────

def get_loaded_bp(
    start_date: Optional[date] = Query(None, description="Start of date range (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End of date range (YYYY-MM-DD)"),
    internal_key: str = Depends(get_syntrillo_internal_key),
) -> BloodPressureAnalysis:
    """
    Instantiate BloodPressureAnalysis and load the patient's BP readings.

    Raises 422 if the date range is too short; 404 if there are no readings.
    Shared across /summary, /analysis, /extremes, and /distribution.
    """
    bp = BloodPressureAnalysis(internal_key)
    _, log = bp.get_blood_pressure_dataframe(start_date=start_date, end_date=end_date)

    if not log.get("success"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=log.get("error", "Failed to retrieve blood pressure data."),
        )

    return bp


# ── /summary ──────────────────────────────────────────────────────────────────

@router.get("/summary", response_model=BPSummaryResponse)
def get_bp_summary(bp: BloodPressureAnalysis = Depends(get_loaded_bp)):
    """
    Key metrics with grades for the most recent (Current/Latest) timeframe.

    Powers the summary card at the top of the BP tab (target vs actual view).
    """
    summary = bp.calculate_summary_stats(hide_intervention=False)
    return BPSummaryResponse(
        date_range=summary.get("date_range"),
        status=GradedMetric(**summary["status"]),
        avg_sbp=GradedMetric(**summary["avg_sbp"]),
        avg_dbp=GradedMetric(**summary["avg_dbp"]),
        peak_sbp=GradedMetric(**summary["peak_sbp"]),
        low_sbp=GradedMetric(**summary["low_sbp"]),
        symptomatic_hypotension=GradedMetric(**summary["symptomatic_hypotension"]),
        near_hypotensive=GradedMetric(**summary["near_hypotensive"]),
    )


# ── /analysis ─────────────────────────────────────────────────────────────────

@router.get("/analysis", response_model=BPAnalysisResponse)
def get_bp_analysis(bp: BloodPressureAnalysis = Depends(get_loaded_bp)):
    """
    Full timeframed analysis table with per-metric grades and progress deltas.

    Powers the detailed metrics table below the summary card.
    """
    return BPAnalysisResponse(**bp.get_analysis_data())


# ── /extremes ─────────────────────────────────────────────────────────────────

@router.get("/extremes", response_model=BPExtremesResponse)
def get_bp_extremes(bp: BloodPressureAnalysis = Depends(get_loaded_bp)):
    """
    Out-of-bounds readings: SBP < 90, SBP > 170, or DBP > 110.
    """
    return BPExtremesResponse(measurements=bp.get_extremes())


# ── /distribution ─────────────────────────────────────────────────────────────

@router.get("/distribution", response_model=BPDistributionResponse)
def get_bp_distribution(bp: BloodPressureAnalysis = Depends(get_loaded_bp)):
    """
    Box-and-whisker statistics for systolic and diastolic readings by hour of day.

    Powers the distribution chart showing when readings tend to be
    highest/lowest and how variable they are throughout the day.
    """
    df = bp.bpm_df.copy()
    df["hour"] = pd.to_datetime(df[TIMESTAMP_LOCAL], errors="coerce").dt.hour

    data = []
    for hour in range(24):
        hour_df = df[df["hour"] == hour].dropna(subset=[SYSTOLIC, DIASTOLIC])
        if hour_df.empty:
            continue
        sbp_stats = _box_plot_stats(hour_df[SYSTOLIC].tolist())
        dbp_stats = _box_plot_stats(hour_df[DIASTOLIC].tolist())
        if sbp_stats is not None and dbp_stats is not None:
            data.append(HourlyDataPoint(
                hour=hour,
                count=len(hour_df),
                systolic=sbp_stats,
                diastolic=dbp_stats,
            ))

    return BPDistributionResponse(data=data)


# ── /hr ───────────────────────────────────────────────────────────────────────

@router.get("/hr", response_model=BPHRResponse)
def get_resting_hr(pseudonyms: dict = Depends(get_pseudonyms)):
    """
    Returns baseline, prior, and current resting heart rate averages.

    Replaces: POST /healthie/iframe_provider_tab/blood_pressure/hr
    """
    healthie_user_id = pseudonyms["healthie_user_id"]
    healthie_utils = HealthieUtils()

    rhr_data = get_healthie_metric_data(healthie_utils, healthie_user_id, category=RHR_CATEGORY)
    pulse_data = get_healthie_metric_data(healthie_utils, healthie_user_id, category="Pulse")
    hr_data = rhr_data if len(rhr_data) >= len(pulse_data) else pulse_data

    hr_metadata = (
        calc_rhr_metadata(hr_data, baseline_num_weeks=2, trailing_num_weeks=2, prior_num_weeks=2)
        if hr_data
        else {}
    )

    return BPHRResponse(
        average_rhr_baseline=hr_metadata.get("average_rhr_baseline"),
        average_rhr_trailing=hr_metadata.get("average_rhr_trailing"),
        average_rhr_prior=hr_metadata.get("average_rhr_prior"),
        baseline_start_date=hr_metadata.get("baseline_start_date"),
        baseline_end_date=hr_metadata.get("baseline_end_date"),
        prior_start_date=hr_metadata.get("prior_start_date"),
        prior_end_date=hr_metadata.get("prior_end_date"),
        current_start_date=hr_metadata.get("current_start_date"),
        current_end_date=hr_metadata.get("current_end_date"),
    )


# ── /biometrics ───────────────────────────────────────────────────────────────

@router.get("/biometrics", response_model=BPBiometricsResponse)
def get_biometrics(
    internal_key: str = Depends(get_syntrillo_internal_key),
    pseudonyms: dict = Depends(get_pseudonyms),
):
    """
    Returns physical activity, BMI, and SSQ data across timeframes.

    Replaces: POST /healthie/iframe_provider_tab/blood_pressure/biometrics
    """
    healthie_user_id = pseudonyms["healthie_user_id"]
    db_manager = SyntrilloDatabaseManager(internal_key)
    healthie_utils = HealthieUtils()

    # ── Physical activity ─────────────────────────────────────────────────────
    physical_activity_form_id, physical_activity_module_id = db_manager.get_form_module_ids_by_module_label(
        "activity_questionnaire_intake"
    )
    _, inactivity_module_id = db_manager.get_form_module_ids_by_module_label(
        "inactivity_questionnaire_intake"
    )

    activity_form_responses = HealthieForms().get_form_answers(
        user_id=healthie_user_id,
        custom_module_form_id=physical_activity_form_id,
    )
    responses_list = (activity_form_responses or {}).get("formAnswerGroups", [])

    activity_baseline = activity_prior = activity_current = None
    inactivity_baseline = inactivity_prior = inactivity_current = None

    if responses_list:
        cleaned = [
            {
                "created_at": r["created_at"],
                "activity_minutes": next(
                    (a["answer"] for a in r["form_answers"] if a["custom_module_id"] == str(physical_activity_module_id)),
                    None,
                ),
                "inactivity_hours": next(
                    (a["answer"] for a in r["form_answers"] if a["custom_module_id"] == str(inactivity_module_id)),
                    None,
                ),
            }
            for r in responses_list
        ]

        if len(cleaned) >= 3:
            activity_baseline = (cleaned[-1]["activity_minutes"], cleaned[-1]["created_at"])
            activity_prior = (cleaned[-2]["activity_minutes"], cleaned[-2]["created_at"])
            activity_current = (cleaned[0]["activity_minutes"], cleaned[0]["created_at"])
            inactivity_baseline = (cleaned[-1]["inactivity_hours"], cleaned[-1]["created_at"])
            inactivity_prior = (cleaned[-2]["inactivity_hours"], cleaned[-2]["created_at"])
            inactivity_current = (cleaned[0]["inactivity_hours"], cleaned[0]["created_at"])
        elif len(cleaned) == 2:
            activity_baseline = (cleaned[-1]["activity_minutes"], cleaned[-1]["created_at"])
            activity_current = (cleaned[0]["activity_minutes"], cleaned[0]["created_at"])
            inactivity_baseline = (cleaned[-1]["inactivity_hours"], cleaned[-1]["created_at"])
            inactivity_current = (cleaned[0]["inactivity_hours"], cleaned[0]["created_at"])
        elif len(cleaned) == 1:
            activity_baseline = (cleaned[0]["activity_minutes"], cleaned[0]["created_at"])
            inactivity_baseline = (cleaned[0]["inactivity_hours"], cleaned[0]["created_at"])

    physical_activity_data = {
        "inactive": {
            "inactivity_baseline": inactivity_baseline,
            "inactivity_prior": inactivity_prior,
            "inactivity_current": inactivity_current,
        },
        "active": {
            "activity_baseline": activity_baseline,
            "activity_prior": activity_prior,
            "activity_current": activity_current,
        },
    }

    # ── BMI ───────────────────────────────────────────────────────────────────
    patient_data = get_patient_info(healthie_user_id=healthie_user_id)
    height = patient_data.get("height")
    weight_data_response = get_healthie_metric_data(healthie_utils, healthie_user_id, category=WEIGHT_CATEGORY)
    bmis = [
        {"bmi": calculate_bmi(w["metric_stat"], height), "date": w["created_at"]}
        for w in weight_data_response
    ]

    bmi_baseline = bmi_prior = bmi_current = None
    if len(bmis) >= 3:
        bmi_baseline, bmi_prior, bmi_current = bmis[0], bmis[-2], bmis[-1]
    elif len(bmis) == 2:
        bmi_baseline, bmi_current = bmis[0], bmis[-1]
    elif len(bmis) == 1:
        bmi_baseline = bmis[0]
    else:
        logger.warning("Patient does not have at least 1 bmi available...")

    bmi_data = {
        "bmi_baseline": bmi_baseline,
        "bmi_prior": bmi_prior,
        "bmi_current": bmi_current,
    }

    # ── SSQ ───────────────────────────────────────────────────────────────────
    secrets_manager = LocalEnvironmentAndSecrets(load_healthie_secrets=True)
    custom_module_form_id = "2455490" if secrets_manager.is_production() else "2203381"

    forms_manager = HealthieForms()
    autoscored_sections = forms_manager.get_autoscored_sections(
        custom_module_form_id=custom_module_form_id,
        user_id=healthie_user_id,
    )

    ssq_baseline = ssq_prior = ssq_current = None
    ssq_baseline_date = ssq_prior_date = ssq_current_date = None

    if autoscored_sections and len(autoscored_sections.get("formAnswerGroups", [])) > 0:
        ssq_responses = autoscored_sections["formAnswerGroups"]
        if len(ssq_responses) >= 3:
            ssq_baseline = ssq_responses[-1]["autoscored_sections"][-1].get("value")
            ssq_baseline_date = ssq_responses[-1].get("created_at")
            ssq_prior = ssq_responses[1]["autoscored_sections"][-1].get("value")
            ssq_prior_date = ssq_responses[1].get("created_at")
            ssq_current = ssq_responses[0]["autoscored_sections"][-1].get("value")
            ssq_current_date = ssq_responses[0].get("created_at")
        elif len(ssq_responses) == 2:
            ssq_baseline = ssq_responses[-1]["autoscored_sections"][-1].get("value")
            ssq_baseline_date = ssq_responses[-1].get("created_at")
            ssq_current = ssq_responses[0]["autoscored_sections"][-1].get("value")
            ssq_current_date = ssq_responses[0].get("created_at")
        elif len(ssq_responses) == 1:
            ssq_baseline = ssq_responses[-1]["autoscored_sections"][-1].get("value")
            ssq_baseline_date = ssq_responses[-1].get("created_at")
        else:
            logger.warning("Patient does not have at least 1 SSQ response...")

    return BPBiometricsResponse(
        physical_activity_data=physical_activity_data,
        bmi_data=bmi_data,
        ssq_data=SSQData(
            ssq_current=ssq_current,
            ssq_prior=ssq_prior,
            ssq_baseline=ssq_baseline,
            ssq_baseline_date=ssq_baseline_date,
            ssq_prior_date=ssq_prior_date,
            ssq_current_date=ssq_current_date,
        ),
    )


# ── /metrics ──────────────────────────────────────────────────────────────────

@router.get("/metrics", response_model=BPMetricsResponse)
def get_bp_metrics(
    internal_key: str = Depends(get_syntrillo_internal_key),
    pseudonyms: dict = Depends(get_pseudonyms),
):
    """
    Returns SSQ score, BMI, and resting heart rate for the patient.

    Replaces: POST /healthie/iframe_provider_tab/blood_pressure/metrics
    """
    healthie_user_id = pseudonyms["healthie_user_id"]

    biometrics = get_biometric_data(internal_key)
    bmi = calculate_bmi(biometrics["weight"], biometrics["height"])

    db_manager = SyntrilloDatabaseManager(internal_key)
    healthie_data = get_srs_healthie_data(healthie_user_id, db_manager, internal_key)
    hr_measurements = HRMeasurements(
        baseline_rhr=healthie_data.get("average_rhr_baseline"),
        trailing_rhr=healthie_data.get("average_rhr_trailing"),
    )

    secrets_manager = LocalEnvironmentAndSecrets(load_healthie_secrets=True)
    custom_module_form_id = "2455490" if secrets_manager.is_production() else "2203381"

    forms_manager = HealthieForms()
    autoscored_sections = forms_manager.get_autoscored_sections(
        custom_module_form_id=custom_module_form_id,
        user_id=healthie_user_id,
    )

    ssq_score = (
        autoscored_sections["formAnswerGroups"][0]["autoscored_sections"]
        if autoscored_sections and len(autoscored_sections.get("formAnswerGroups", [])) > 0
        else None
    )

    return BPMetricsResponse(ssq_score=ssq_score, bmi=bmi, hr_measurements=hr_measurements)


# ── /download ─────────────────────────────────────────────────────────────────

@router.get("/download")
def download_bp_report(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    file_name: Optional[str] = Query(None),
    include_intro_section: bool = Query(True),
    internal_key: str = Depends(get_syntrillo_internal_key),
    pseudonyms: dict = Depends(get_pseudonyms),
):
    """
    Streams a PDF blood pressure report.

    Uses LegacyBPAnalysis (from bp_analysis) because BloodPressureReport
    requires DataFrames (timeframed_df, extremes_df) that the new
    BloodPressureAnalysis class does not expose.

    Analysis is computed server-side; the client no longer sends
    pre-rendered JSON (unlike the legacy download endpoint).

    Replaces: GET/POST /healthie/iframe_provider_tab/blood_pressure/download
    """
    healthie_user = HealthieUser(pseudonyms["healthie_user_id"])
    patient_info = healthie_user._patient_information or {}
    first_initial = (patient_info.get("first_name") or " ")[0]
    last_initial = (patient_info.get("last_name") or " ")[0]

    date_str = datetime.now().strftime("%y%m%d")
    resolved_name = (file_name or f"{first_initial}{last_initial}-{date_str}").strip()

    bp = LegacyBPAnalysis(internal_key)
    _, log = bp.get_blood_pressure_dataframe(start_date=start_date, end_date=end_date)

    if not log.get("success") or _.empty:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No blood pressure data available for this report.",
        )

    analysis_table = bp.get_analysis_table()
    analysis_table = analysis_table[~analysis_table.index.isin(_ROWS_TO_REMOVE)]
    analysis_table.rename(index=_ROW_RENAME, inplace=True)
    extremes = bp.calculate_extremes().reset_index(drop=True)
    summary_stats = bp.calculate_summary_stats(hide_intervention=True)

    nanoid = "".join(secrets.choice(string.ascii_letters + string.digits) for _ in range(5))
    resolved_name = f"{resolved_name}-{nanoid}"

    bp_report = BloodPressureReport(
        logo=None,
        patient_info_dict=patient_info,
        summary_dict=summary_stats,
        timeframed_df=analysis_table,
        extremes_df=extremes,
        report_code=nanoid,
    )

    pdf_buffer = (
        bp_report.generate_provider_pdf_report()
        if include_intro_section
        else bp_report.generate_patient_pdf_report()
    )

    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{resolved_name}.pdf"'},
    )


# ── Private helpers ───────────────────────────────────────────────────────────

def _box_plot_stats(values: list) -> Optional[BoxPlotStats]:
    """
    Compute 1.5×IQR box-and-whisker statistics for a list of numeric values.

    Whiskers extend to the most extreme non-outlier data points; values
    beyond the fences are listed separately as outliers.
    Returns None if the list is empty after dropping NaNs.
    """
    clean = [v for v in values if v is not None and not (isinstance(v, float) and np.isnan(v))]
    if not clean:
        return None

    arr = np.array(clean, dtype=float)
    q1 = float(np.percentile(arr, 25))
    q3 = float(np.percentile(arr, 75))
    iqr = q3 - q1
    lower_fence = q1 - 1.5 * iqr
    upper_fence = q3 + 1.5 * iqr

    non_outliers = [v for v in clean if lower_fence <= v <= upper_fence]
    outliers = [v for v in clean if v < lower_fence or v > upper_fence]

    return BoxPlotStats(
        min=float(min(non_outliers)) if non_outliers else float(min(clean)),
        q1=q1,
        median=float(np.median(arr)),
        mean=float(np.mean(arr)),
        q3=q3,
        max=float(max(non_outliers)) if non_outliers else float(max(clean)),
        outliers=outliers,
    )

