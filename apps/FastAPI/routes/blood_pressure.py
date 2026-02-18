"""
Blood pressure routes — FastAPI port of the legacy Flask blueprint.

Legacy route → new endpoint mapping:
  POST /healthie/iframe_provider_tab/blood_pressure/analysis   → GET  /api/v1/blood-pressure/analysis
  GET  /healthie/iframe_provider_tab/blood_pressure/download   → GET  /api/v1/blood-pressure/download
  POST /healthie/iframe_provider_tab/blood_pressure/metrics    → GET  /api/v1/blood-pressure/metrics
  POST /healthie/iframe_provider_tab/blood_pressure/hr         → GET  /api/v1/blood-pressure/hr
  POST /healthie/iframe_provider_tab/blood_pressure/biometrics → GET  /api/v1/blood-pressure/biometrics

Key differences from the legacy implementation:
  - No HTML is returned; React handles all rendering.
  - patient_not_registered_at_syntrillo is handled by a 403 from the
    dependency layer rather than rendering a template.
  - PDF download re-computes analysis server-side instead of accepting
    pre-rendered JSON from the client.
  - All endpoints accept temporary_lookup_code as a query parameter so
    FastAPI's dependency injection can cache the identity resolution
    within a single request.
"""

import secrets
import string
import sys
from datetime import date
from pathlib import Path
from typing import Optional

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse

SOURCES_PATH = Path(__file__).resolve().parents[3] / "sources"
sys.path.insert(0, str(SOURCES_PATH))

from syntrillo.api_healthie.constants import RHR_CATEGORY, WEIGHT_CATEGORY
from syntrillo.api_healthie.forms import HealthieForms
from syntrillo.api_healthie.user import HealthieUser
from syntrillo.api_healthie.utils import HealthieUtils
from syntrillo.bp_analysis.bp_analysis import BloodPressureAnalysis
from syntrillo.bp_analysis.bp_report import BloodPressureReport
from syntrillo.pseudonyms_management.lookup_codes_management import LookUpCodesManagement
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
    AnalysisRow,
    BPAnalysisResponse,
    BPBiometricsResponse,
    BPHRResponse,
    BPMeasurement,
    BPMetricsResponse,
    DateRange,
    GradedValue,
    HRMeasurements,
    SSQData,
    SummaryStats,
)

router = APIRouter()

# Rows suppressed in the legacy route (kept consistent here)
_ROWS_TO_REMOVE = {"SBP CV (%)", "DBP CV (%)", "SBP Count (>= 175)"}
_ROW_RENAME = {"Hypotensive Count⁴": "Near-Hypotensive Events⁴"}


# ── /analysis ─────────────────────────────────────────────────────────────────

@router.get("/analysis", response_model=BPAnalysisResponse)
def get_bp_analysis(
    start_date: Optional[date] = Query(None, description="Start of date range (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End of date range (YYYY-MM-DD)"),
    internal_key: str = Depends(get_syntrillo_internal_key),
):
    """
    Returns structured blood pressure analysis for a given date range.

    Replaces: POST /healthie/iframe_provider_tab/blood_pressure/analysis
    """
    bp = BloodPressureAnalysis(internal_key)
    _, log = bp.get_blood_pressure_dataframe(start_date=start_date, end_date=end_date)

    if not log.get("success"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=log.get("error", "Failed to retrieve blood pressure data."),
        )

    if _.empty:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Insufficient data. Patient has recorded zero measurements.",
        )

    summary_stats = bp.calculate_summary_stats(hide_intervention=False)
    analysis_table = bp.get_analysis_table()
    analysis_table = analysis_table[~analysis_table.index.isin(_ROWS_TO_REMOVE)]
    analysis_table.rename(index=_ROW_RENAME, inplace=True)
    extremes = bp.calculate_extremes().reset_index(drop=True)

    return BPAnalysisResponse(
        analysis=_df_to_analysis_rows(analysis_table),
        extremes=_df_to_extremes(extremes),
        summary_stats=_dict_to_summary_stats(summary_stats),
    )


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

    Analysis is computed server-side; the client no longer needs to send
    pre-rendered JSON (unlike the legacy download endpoint).

    Replaces: GET/POST /healthie/iframe_provider_tab/blood_pressure/download
    """
    healthie_user = HealthieUser(pseudonyms["healthie_user_id"])
    patient_info = healthie_user._patient_information or {}
    first_initial = (patient_info.get("first_name") or " ")[0]
    last_initial = (patient_info.get("last_name") or " ")[0]

    from datetime import datetime
    date_str = datetime.now().strftime("%y%m%d")
    resolved_name = (file_name or f"{first_initial}{last_initial}-{date_str}").strip()

    bp = BloodPressureAnalysis(internal_key)
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


# ── /hr ───────────────────────────────────────────────────────────────────────

@router.get("/hr", response_model=BPHRResponse)
def get_resting_hr(
    pseudonyms: dict = Depends(get_pseudonyms),
):
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


# ── Private helpers ───────────────────────────────────────────────────────────

def _df_to_analysis_rows(df: pd.DataFrame) -> list[AnalysisRow]:
    return [
        AnalysisRow(
            metric=str(metric),
            baseline=row.get("Baseline"),
            prior=row.get("Prior"),
            current=row.get("Current"),
            since_baseline=row.get("Since Baseline"),
            since_prior=row.get("Since Prior"),
        )
        for metric, row in df.iterrows()
    ]


def _df_to_extremes(df: pd.DataFrame) -> list[BPMeasurement]:
    if df is None or df.empty:
        return []
    return [
        BPMeasurement(
            timestamp=str(row.get("Timestamp", "")),
            systolic=float(row.get("Systolic", 0)),
            diastolic=float(row.get("Diastolic", 0)),
        )
        for _, row in df.iterrows()
    ]


def _dict_to_summary_stats(summary: dict) -> SummaryStats:
    def to_graded(d: dict) -> GradedValue:
        return GradedValue(value=d.get("value"), grade=int(d.get("grade", 0)))

    def to_date_range(dr) -> DateRange:
        if isinstance(dr, dict):
            return DateRange(start=dr.get("start"), end=dr.get("end"))
        return DateRange()

    return SummaryStats(
        date_range=to_date_range(summary.get("date_range", {})),
        status=to_graded(summary.get("status", {})),
        avg_sbp=to_graded(summary.get("avg_sbp", {})),
        avg_dbp=to_graded(summary.get("avg_dbp", {})),
        peak_sbp=to_graded(summary.get("peak_sbp", {})),
        low_sbp=to_graded(summary.get("low_sbp", {})),
        symptomatic_hypotension=to_graded(summary.get("symptomatic_hypotension", {})),
        near_hypotensive=to_graded(summary.get("near_hypotensive", {})),
    )