/**
 * TypeScript types for the risk score and lab values API responses.
 * Mirrors the FastAPI Pydantic schemas in apps/FastAPI/schemas/risk_score.py.
 */

// ── GET /api/v1/risk-score/data ───────────────────────────────────────────────

export interface RiskScoreResponse {
  success: boolean;
  message?: string | null;
  risk_score?: number | null;
  priority_score?: number | null;
  metrics?: Record<string, any> | null;
  independent_risk_variable_scores?: Record<string, any> | null;
  dependent_risk_variable_contributions?: Record<string, any> | null;
}

// ── GET /api/v1/risk-score/lab-values ────────────────────────────────────────

export interface LabValuesResponse {
  hemoglobin_a1c?: number | null;
  ldl?: number | null;
  hdl?: number | null;
  triglycerides?: number | null;
  creatinine?: number | null;
}
