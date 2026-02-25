"""
Pydantic schemas for the risk score and lab values features.

Endpoint → schema mapping:
  GET /api/v1/risk-score/data       → RiskScoreResponse
  GET /api/v1/risk-score/lab-values → LabValuesResponse
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import BaseModel


# ── GET /data ─────────────────────────────────────────────────────────────────

class RiskScoreResponse(BaseModel):
    """
    Risk score and priority score with supporting metrics.

    Mirrors the JSON returned by:
      POST /healthie/iframe_provider_tab/risk_score/data
    """
    success: bool
    message: Optional[str] = None
    risk_score: Optional[float] = None
    priority_score: Optional[float] = None
    metrics: Optional[Dict[str, Any]] = None
    independent_risk_variable_scores: Optional[Dict[str, Any]] = None
    dependent_risk_variable_contributions: Optional[Dict[str, Any]] = None


# ── GET /lab-values ───────────────────────────────────────────────────────────

class LabValuesResponse(BaseModel):
    """
    Patient lab values extracted from the risk score metrics.lab_data.

    All fields are optional — a value is None when the patient has no
    recorded entry for that lab marker.
    """
    hemoglobin_a1c: Optional[float] = None
    ldl: Optional[float] = None
    hdl: Optional[float] = None
    triglycerides: Optional[float] = None
    creatinine: Optional[float] = None
