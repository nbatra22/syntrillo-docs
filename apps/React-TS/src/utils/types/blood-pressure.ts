// ── Shared ────────────────────────────────────────────────────────────────────

/** Grade scale: 0 = optimal, 1 = caution, 2 = critical, 3 = severe. */
export type Grade = 0 | 1 | 2 | 3;

export interface GradedMetric {
  value: number | string | null;
  grade: Grade;
}


// ── GET /summary ──────────────────────────────────────────────────────────────

export interface BPSummaryResponse {
  date_range: string | null;
  status: GradedMetric;
  avg_sbp: GradedMetric;
  avg_dbp: GradedMetric;
  peak_sbp: GradedMetric;
  low_sbp: GradedMetric;
  symptomatic_hypotension: GradedMetric;
  near_hypotensive: GradedMetric;
}


// ── GET /analysis ─────────────────────────────────────────────────────────────

export interface TimeframeInfo {
  name: string;
  date_range: string;
}

export interface MetricValue {
  value: number | null;
  /** null means no colour coding for this metric. */
  grade: number | null;
}

export interface ProgressDelta {
  delta_pts: number;
  direction: 'improving' | 'worsening' | 'same';
}

export interface MetricProgress {
  since_baseline: ProgressDelta | null;
  since_prior: ProgressDelta | null;
}

export interface AnalysisRow {
  metric: string;
  /** Keyed by timeframe name e.g. "Baseline", "Prior", "Current". */
  values: Record<string, MetricValue>;
  progress: MetricProgress;
}

export interface OverallProgress {
  since_baseline: ProgressDelta | null;
  since_prior: ProgressDelta | null;
}

export interface BPAnalysisResponse {
  timeframes: TimeframeInfo[];
  rows: AnalysisRow[];
  overall_progress: OverallProgress;
}


// ── GET /extremes ─────────────────────────────────────────────────────────────

export interface BPMeasurement {
  timestamp: string;
  systolic: number;
  diastolic: number;
}

export interface BPExtremesResponse {
  measurements: BPMeasurement[];
}


// ── GET /distribution ─────────────────────────────────────────────────────────

export interface BoxPlotStats {
  min: number;
  q1: number;
  median: number;
  mean: number;
  q3: number;
  max: number;
  outliers: number[];
}

export interface HourlyDataPoint {
  hour: number;
  count: number;
  systolic: BoxPlotStats;
  diastolic: BoxPlotStats;
}

export interface BPDistributionResponse {
  data: HourlyDataPoint[];
}


// ── GET /hr ───────────────────────────────────────────────────────────────────

export interface BPHRResponse {
  average_rhr_baseline: number | null;
  average_rhr_trailing: number | null;
  average_rhr_prior: number | null;
  baseline_start_date: string | null;
  baseline_end_date: string | null;
  prior_start_date: string | null;
  prior_end_date: string | null;
  current_start_date: string | null;
  current_end_date: string | null;
}


// ── GET /biometrics ───────────────────────────────────────────────────────────

export interface BMIDataPoint {
  bmi: number | null;
  date: string | null;
}

/** Activity tuple: [value, recorded_at] as returned from Healthie forms. */
type ActivityTuple = [string, string] | null;

export interface BPBiometricsResponse {
  physical_activity_data: {
    inactive: {
      inactivity_baseline: ActivityTuple;
      inactivity_prior: ActivityTuple;
      inactivity_current: ActivityTuple;
    };
    active: {
      activity_baseline: ActivityTuple;
      activity_prior: ActivityTuple;
      activity_current: ActivityTuple;
    };
  };
  bmi_data: {
    bmi_baseline: BMIDataPoint | null;
    bmi_prior: BMIDataPoint | null;
    bmi_current: BMIDataPoint | null;
  };
  ssq_data: {
    ssq_current: unknown;
    ssq_prior: unknown;
    ssq_baseline: unknown;
    ssq_baseline_date: string | null;
    ssq_prior_date: string | null;
    ssq_current_date: string | null;
  };
}


// ── GET /metrics ──────────────────────────────────────────────────────────────

export interface HRMeasurements {
  baseline_rhr: number | null;
  trailing_rhr: number | null;
}

export interface BPMetricsResponse {
  /** Raw Healthie autoscored SSQ sections. Shape depends on form configuration. */
  ssq_score: unknown;
  bmi: number | null;
  hr_measurements: HRMeasurements;
}


// ── Shared request params ─────────────────────────────────────────────────────

export interface BPDateRangeParams {
  startDate?: string; // YYYY-MM-DD
  endDate?: string;   // YYYY-MM-DD
}