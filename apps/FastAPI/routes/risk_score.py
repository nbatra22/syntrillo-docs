"""
Risk score routes — FastAPI port of the legacy Flask blueprint.

Legacy route → new endpoint mapping:
  POST /healthie/iframe_provider_tab/risk_score/data → GET /api/v1/risk-score/data
                                                        GET /api/v1/risk-score/lab-values

Key differences from the legacy implementation:
  - No HTML is returned; React handles all rendering.
  - Lab values are split into a focused sub-endpoint so the frontend
    can fetch them independently from the full risk score payload.
  - temporary_lookup_code resolves to syntrillo_internal_key via
    the shared get_syntrillo_internal_key dependency.
"""

import sys
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status

SOURCES_PATH = Path(__file__).resolve().parents[3] / "sources"
sys.path.insert(0, str(SOURCES_PATH))

from syntrillo.stroke_risk_score_v2.calc_risk_score import calculate_risk_score
from syntrillo.system.logger import logger

from dependencies import get_syntrillo_internal_key
from schemas.risk_score import LabValuesResponse, RiskScoreResponse

router = APIRouter()


# ── /data ─────────────────────────────────────────────────────────────────────

@router.get("/data", response_model=RiskScoreResponse)
def get_risk_score_data(
    internal_key: str = Depends(get_syntrillo_internal_key),
):
    """
    Risk score and priority score with supporting metrics.

    Replaces: POST /healthie/iframe_provider_tab/risk_score/data
    """
    try:
        risk_score, metrics, priority_score, independent_scores, dependent_contributions = (
            calculate_risk_score(internal_key, is_ondemand_srs=False)
        )

        if risk_score is None and priority_score is None:
            return RiskScoreResponse(
                success=True,
                message="No data available",
                risk_score=None,
                priority_score=None,
                metrics=metrics,
                independent_risk_variable_scores=independent_scores,
                dependent_risk_variable_contributions=dependent_contributions,
            )

        # Serialize Pydantic sub-models that calculate_risk_score may return
        if metrics and metrics.get("srs_response_data") is not None:
            metrics["srs_response_data"] = metrics["srs_response_data"][0].model_dump()
        if metrics and metrics.get("lab_data") is not None:
            metrics["lab_data"] = metrics["lab_data"].model_dump()

        return RiskScoreResponse(
            success=True,
            message="Risk score data retrieved successfully",
            risk_score=risk_score,
            priority_score=priority_score,
            metrics=metrics,
            independent_risk_variable_scores=independent_scores,
            dependent_risk_variable_contributions=dependent_contributions,
        )

    except Exception as e:
        logger.error(f"Error retrieving risk score data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve risk score data.",
        )


# ── /lab-values ───────────────────────────────────────────────────────────────

@router.get("/lab-values", response_model=LabValuesResponse)
def get_lab_values(
    internal_key: str = Depends(get_syntrillo_internal_key),
):
    """
    Lab values extracted from the risk score metrics (HbA1c, LDL, HDL,
    Triglycerides, Creatinine).

    Calls calculate_risk_score internally and extracts metrics.lab_data.
    Returns None for any value the patient has not yet recorded.
    """
    try:
        _, metrics, _, _, _ = calculate_risk_score(internal_key, is_ondemand_srs=False)

        lab_data = metrics.get("lab_data") if metrics else None

        if lab_data is None:
            return LabValuesResponse()

        # lab_data may be a Pydantic model or already a dict
        if hasattr(lab_data, "model_dump"):
            lab_data = lab_data.model_dump()

        return LabValuesResponse(
            hemoglobin_a1c=lab_data.get("HemoglobinA1c"),
            ldl=lab_data.get("LDL"),
            hdl=lab_data.get("HDL"),
            triglycerides=lab_data.get("Triglycerides"),
            creatinine=lab_data.get("Creatinine"),
        )

    except Exception as e:
        logger.error(f"Error retrieving lab values: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve lab values.",
        )
