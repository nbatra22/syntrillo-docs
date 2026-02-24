import { buildQueryString, fetchBlob, get } from './helpers';
import type {
  BPAnalysisResponse,
  BPBiometricsResponse,
  BPDateRangeParams,
  BPDistributionResponse,
  BPExtremesResponse,
  BPHRResponse,
  BPMetricsResponse,
  BPSummaryResponse,
} from '../types/blood-pressure';

// const BASE = '/api/v1/blood-pressure';
const BASE = 'http://127.0.0.1:8000/api/v1/blood-pressure';

function params(
  temporaryLookupCode: string,
  dateRange?: BPDateRangeParams,
  extra?: Record<string, string | number | boolean | null | undefined>,
): string {
  return buildQueryString({
    temporary_lookup_code: temporaryLookupCode,
    start_date: dateRange?.startDate,
    end_date: dateRange?.endDate,
    ...extra,
  });
}


// ── Endpoints ─────────────────────────────────────────────────────────────────

export const bloodPressureApi = {

  /** Key metrics with grades for the most recent timeframe. Powers the summary card. */
  getBPSummary: (
    temporaryLookupCode: string,
    dateRange?: BPDateRangeParams,
  ): Promise<BPSummaryResponse> =>
    get(`${BASE}/summary?${params(temporaryLookupCode, dateRange)}`),

  /** Full timeframed analysis table with per-metric grades and progress deltas. */
  getBPAnalysis: (
    temporaryLookupCode: string,
    dateRange?: BPDateRangeParams,
  ): Promise<BPAnalysisResponse> =>
    get(`${BASE}/analysis?${params(temporaryLookupCode, dateRange)}`),

  /** Out-of-bounds readings: SBP < 90, SBP > 170, or DBP > 110. */
  getBPExtremes: (
    temporaryLookupCode: string,
    dateRange?: BPDateRangeParams,
  ): Promise<BPExtremesResponse> =>
    get(`${BASE}/extremes?${params(temporaryLookupCode, dateRange)}`),

  /** Hourly box-and-whisker distribution data for the spread chart. */
  getBPDistribution: (
    temporaryLookupCode: string,
    dateRange?: BPDateRangeParams,
  ): Promise<BPDistributionResponse> =>
    get(`${BASE}/distribution?${params(temporaryLookupCode, dateRange)}`),

  /** Resting heart rate averages across baseline, prior, and current timeframes. */
  getBPHR: (
    temporaryLookupCode: string,
  ): Promise<BPHRResponse> =>
    get(`${BASE}/hr?${params(temporaryLookupCode)}`),

  /** Physical activity, BMI history, and SSQ scores across timeframes. */
  getBPBiometrics: (
    temporaryLookupCode: string,
  ): Promise<BPBiometricsResponse> =>
    get(`${BASE}/biometrics?${params(temporaryLookupCode)}`),

  /** Quick scalar metrics (SSQ, BMI, RHR) — no date range required. */
  getBPMetrics: (
    temporaryLookupCode: string,
  ): Promise<BPMetricsResponse> =>
    get(`${BASE}/metrics?${params(temporaryLookupCode)}`),

  /**
   * Fetch a PDF report as a Blob.
   * Pass the result to triggerDownload() from helpers to prompt the save dialog.
   *
   * @example
   * const blob = await bloodPressureApi.downloadBPReport(code, {}, 'JD-250101');
   * triggerDownload(blob, 'report.pdf');
   */
  downloadBPReport: (
    temporaryLookupCode: string,
    dateRange?: BPDateRangeParams,
    fileName?: string,
    includeIntroSection = true,
  ): Promise<Blob> =>
    fetchBlob(`${BASE}/download?${params(temporaryLookupCode, dateRange, {
      file_name: fileName,
      include_intro_section: includeIntroSection,
    })}`),
};
