import { buildQueryString, get } from './helpers';
import type { LabValuesResponse, RiskScoreResponse } from '../types/risk-score';

// const BASE = '/api/v1/risk-score';
const BASE = 'http://127.0.0.1:8000/api/v1/risk-score';

function params(temporaryLookupCode: string): string {
  return buildQueryString({ temporary_lookup_code: temporaryLookupCode });
}


// ── Endpoints ─────────────────────────────────────────────────────────────────

export const riskScoreApi = {

  /** Risk score, priority score, and supporting metrics. */
  getRiskScore: (temporaryLookupCode: string): Promise<RiskScoreResponse> =>
    get(`${BASE}/data?${params(temporaryLookupCode)}`),

  /** Patient lab values (HbA1c, LDL, HDL, triglycerides, creatinine). */
  getLabValues: (temporaryLookupCode: string): Promise<LabValuesResponse> =>
    get(`${BASE}/lab-values?${params(temporaryLookupCode)}`),
};
