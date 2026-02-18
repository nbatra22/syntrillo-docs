"""
React-ready blood pressure analysis class.

Mirrors the logic of bp_analysis/bp_analysis.py with the following changes:

  - get_analysis_data() replaces get_analysis_table().
    Returns a structured dict (not a DataFrame) with per-metric grades
    pre-computed, so React can colour-code without any additional logic.

  - get_extremes() replaces calculate_extremes().
    Returns a list of dicts instead of a DataFrame.

  - Progress deltas in get_analysis_data() are numeric dicts
    ({"delta_pts": int, "direction": str}) instead of the legacy string
    symbols ("+2", "-2", "=").

  - style_row(), wrap_text(), and generate_custom_report() are removed.
    Presentation is handled by the React frontend.

  - SBP CV (%), DBP CV (%), and SBP Count (>= 175) are excluded from the
    analysis rows (they were filtered in the legacy route layer).

  - "Hypotensive Count" is surfaced as "Near-Hypotensive Events" to match
    the rename applied in the legacy route.

Grade scale used throughout: 0 = optimal, 1 = caution, 2 = critical.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional, Tuple

import pandas as pd

from syntrillo.api_healthie.forms import HealthieForms
from syntrillo.api_tenovi.device_measurements import DeviceMeasurements
from syntrillo.api_tenovi.device_types import DeviceTypes
from syntrillo.bp_analysis.constants import (
    AVG_DBP,
    AVG_PP,
    AVG_SBP,
    DATE_RANGE,
    DBP_CV,
    DBP_SD,
    DIASTOLIC,
    ENGAGEMENT,
    HYPOTENSIVE_COUNT,
    LOW_DBP,
    LOW_SBP,
    MEASUREMENT_COUNT,
    PEAK_DBP,
    PEAK_SBP,
    SBP_COUNT_170,
    SBP_COUNT_175,
    SBP_CV,
    SBP_SD,
    SYSTOLIC,
    TIMESTAMP_LOCAL,
)
from syntrillo.pseudonyms_management.lookup_codes_management import LookUpCodesManagement
from syntrillo.remote_monitoring.syntrillo_database_manager import SyntrilloDatabaseManager
from syntrillo.system.logger import logger


class BloodPressureAnalysis:
    """
    Patient-level blood pressure analysis returning plain Python structures
    suitable for direct JSON serialisation.
    """

    HYPERTENSION_SBP_THRESHOLD = 170
    HYPERTENSION_DBP_THRESHOLD = 110
    HYPOTENSION_SBP_THRESHOLD = 95

    # Ordered list of metrics exposed in the analysis table.
    # SBP CV, DBP CV, and SBP Count >= 175 are intentionally excluded.
    _ANALYSIS_METRICS = [
        MEASUREMENT_COUNT,
        AVG_SBP,
        AVG_DBP,
        AVG_PP,
        PEAK_SBP,
        PEAK_DBP,
        LOW_SBP,
        LOW_DBP,
        SBP_SD,
        DBP_SD,
        SBP_COUNT_170,
        HYPOTENSIVE_COUNT,
        ENGAGEMENT,
    ]

    # Human-readable overrides for metric names that differ from the constant.
    _METRIC_DISPLAY_NAMES = {
        HYPOTENSIVE_COUNT: "Near-Hypotensive Events",
    }

    # Metrics that participate in the progress point system.
    # "boundary" = the unhealthy threshold above which comparisons are meaningful.
    # "threshold" = used by Peak metrics to detect a threshold crossing.
    _PROGRESS_METRICS = {
        AVG_SBP:  {"points": 2, "boundary": 130},
        AVG_DBP:  {"points": 2, "boundary": 80},
        PEAK_SBP: {"points": 2, "threshold": 170, "boundary": 170},
        PEAK_DBP: {"points": 2, "threshold": 110, "boundary": 110},
    }

    def __init__(self, syntrillo_internal_key: uuid.UUID = None) -> None:
        self.syntrillo_internal_key = syntrillo_internal_key
        self.syntrillo_database_manager = SyntrilloDatabaseManager(syntrillo_internal_key)
        self.bpm_df: Optional[pd.DataFrame] = None
        self.timeframed_data: Optional[dict] = None
        self.metadata: Optional[dict] = None

    # ── Data retrieval ────────────────────────────────────────────────────────

    def get_blood_pressure_dataframe(
        self,
        start_date: datetime = None,
        end_date: datetime = None,
    ) -> Tuple[pd.DataFrame, dict]:
        """
        Fetch blood pressure readings from the Tenovi device database.

        Returns:
            (DataFrame, log) where DataFrame has columns:
                timestamp_local, systolic, diastolic
        """
        if start_date is None:
            first_record, _ = self.syntrillo_database_manager.get_first_tenovi_device_data(
                device_name=DeviceTypes.TENOVI_DEVICE_NAME__BPM_PREFIX
            )
            if first_record is not None:
                start_date = datetime.strptime(first_record["timestamp_local"], "%Y-%m-%dT%H:%M:%S.%f%z")
            else:
                start_date = datetime(2000, 1, 1)

        if end_date is None:
            end_date = datetime.now()

        start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=0)

        tz_utc = timezone.utc
        if (end_date.astimezone(tz_utc) - start_date.astimezone(tz_utc)).days < 2:
            return None, {"success": False, "error": "Report period is too short"}

        bpm_df, log = self.syntrillo_database_manager.get_tenovi_device_metric_data(
            metric_name=DeviceMeasurements.TENOVI_METRICS_BPM_BLOOD_PRESSURE,
            start_date=start_date,
            end_date=end_date,
        )

        if bpm_df is None or bpm_df.empty or not log["success"]:
            logger.warning(f"No blood pressure data found for patient {self.syntrillo_internal_key}")
            return None, {"success": False, "error": "No blood pressure data found.", "log": log}

        bpm_df = bpm_df.rename(columns={"value_1": "systolic", "value_2": "diastolic"})
        bpm_df = bpm_df.drop(columns=["device_name", "metric_name"])
        bpm_df["systolic"] = pd.to_numeric(bpm_df["systolic"], errors="coerce")
        bpm_df["diastolic"] = pd.to_numeric(bpm_df["diastolic"], errors="coerce")

        self.bpm_df = bpm_df
        return bpm_df, log

    # ── Timeframe segmentation ────────────────────────────────────────────────

    def calculate_timeframes(self) -> dict:
        """
        Segment bpm_df into Baseline (first 2 weeks), Prior (2 weeks before
        Current), and Current / Latest (most recent 2 weeks).

        Returns:
            {
                "Baseline": ("date_range_str", DataFrame),
                "Prior":    ("date_range_str", DataFrame),
                "Current":  ("date_range_str", DataFrame),
            }
        """
        if self.bpm_df is None:
            self.get_blood_pressure_dataframe()

        df = self.bpm_df
        latest_date = df[TIMESTAMP_LOCAL].max()
        baseline_start = df[TIMESTAMP_LOCAL].min()
        total_weeks = (latest_date - baseline_start).days / 7

        current_start = latest_date - pd.Timedelta(weeks=2)
        baseline_end = baseline_start + pd.Timedelta(weeks=2)
        prior_end = current_start - pd.Timedelta(days=1)
        prior_start = prior_end - pd.Timedelta(weeks=2)
        min_measurements = 3

        def is_valid(tf_df):
            return len(tf_df.dropna()) >= min_measurements and tf_df.notna().any().any()

        timeframes = {}

        baseline_df = df[(df[TIMESTAMP_LOCAL] >= baseline_start) & (df[TIMESTAMP_LOCAL] < baseline_end)]
        if total_weeks >= 4 and is_valid(baseline_df):
            timeframes["Baseline"] = (
                f"{baseline_start.strftime('%-m/%-d/%y')} - {baseline_end.strftime('%-m/%-d/%y')}",
                baseline_df,
            )

        prior_df = df[(df[TIMESTAMP_LOCAL] >= prior_start) & (df[TIMESTAMP_LOCAL] < prior_end)]
        if total_weeks >= 5 and is_valid(prior_df):
            timeframes["Prior"] = (
                f"{prior_start.strftime('%-m/%-d/%y')} - {prior_end.strftime('%-m/%-d/%y')}",
                prior_df,
            )

        current_df = df[df[TIMESTAMP_LOCAL] >= current_start]
        if is_valid(current_df):
            today = datetime.now().date()
            latest_date_only = latest_date.date() if isinstance(latest_date, pd.Timestamp) else latest_date
            label = "Current" if (today - latest_date_only).days <= 5 else "Latest"
            timeframes[label] = (
                f"{current_start.strftime('%-m/%-d/%y')} - {latest_date.strftime('%-m/%-d/%y')}",
                current_df,
            )

        self.timeframed_data = timeframes
        return timeframes

    # ── Metadata calculation ──────────────────────────────────────────────────

    def calculate_aggregated_metadata(self) -> dict:
        """Compute per-timeframe metric metadata."""
        if self.timeframed_data is None:
            self.calculate_timeframes()

        if self.metadata is None:
            self.metadata = {}

        for timeframe, (date_range, df) in self.timeframed_data.items():
            self.metadata[timeframe] = self.calculate_timeframe_metadata(df=df, date_range=date_range)

        return self.metadata

    def calculate_timeframe_metadata(self, df: pd.DataFrame, date_range: str = None) -> dict:
        """
        Compute the 13 analysis metrics for a single timeframe DataFrame.
        Mirrors the legacy calculate_timeframe_metadata() exactly.
        """
        data = {
            DATE_RANGE: date_range,
            MEASUREMENT_COUNT: 0,
            AVG_SBP: None,
            AVG_DBP: None,
            AVG_PP: None,
            PEAK_SBP: None,
            PEAK_DBP: None,
            LOW_SBP: None,
            LOW_DBP: None,
            SBP_SD: None,
            DBP_SD: None,
            SBP_CV: None,
            DBP_CV: None,
            SBP_COUNT_170: 0,
            SBP_COUNT_175: 0,
            HYPOTENSIVE_COUNT: 0,
        }

        if df.empty:
            return data

        data[MEASUREMENT_COUNT] = len(df)
        data[AVG_SBP] = round(df[SYSTOLIC].mean(), 1)
        data[AVG_DBP] = round(df[DIASTOLIC].mean(), 1)
        data[AVG_PP] = round(data[AVG_SBP] - data[AVG_DBP], 1)
        data[PEAK_SBP] = round(df[SYSTOLIC].nlargest(3).mean(), 1)
        data[PEAK_DBP] = round(df[DIASTOLIC].nlargest(3).mean(), 1)
        data[LOW_SBP] = round(df[SYSTOLIC].nsmallest(3).mean(), 1)
        data[LOW_DBP] = round(df[DIASTOLIC].nsmallest(3).mean(), 1)
        data[SBP_SD] = round(df[SYSTOLIC].std(), 1)
        data[DBP_SD] = round(df[DIASTOLIC].std(), 1)
        data[SBP_CV] = round((data[SBP_SD] / data[AVG_SBP]) * 100, 1) if data[AVG_SBP] else None
        data[DBP_CV] = round((data[DBP_SD] / data[AVG_DBP]) * 100, 1) if data[AVG_DBP] else None
        data[SBP_COUNT_170] = len(df[df[SYSTOLIC] >= 170])
        data[SBP_COUNT_175] = len(df[df[SYSTOLIC] >= 175])
        data[HYPOTENSIVE_COUNT] = len(df[df[SYSTOLIC] <= self.HYPOTENSION_SBP_THRESHOLD])
        data[ENGAGEMENT] = self.calculate_engagement(df) if len(df) > 0 else 0.0

        return data

    def calculate_engagement(self, df: pd.DataFrame) -> float:
        """Percentage of days in the timeframe that had at least one reading."""
        df = df.copy()
        df[TIMESTAMP_LOCAL] = pd.to_datetime(df[TIMESTAMP_LOCAL], errors="coerce")
        start = df[TIMESTAMP_LOCAL].min()
        end = df[TIMESTAMP_LOCAL].max()
        total_days = (end - start).days
        days_with_readings = df[TIMESTAMP_LOCAL].dt.date.nunique()
        if total_days == 0:
            return 0.0
        return round((days_with_readings / total_days) * 100, 1)

    # ── Summary statistics ────────────────────────────────────────────────────

    def calculate_summary_stats(self, hide_intervention: bool = True) -> dict:
        """
        Return graded summary statistics for the active (Current/Latest) timeframe.
        Identical logic to the legacy class; return shape is unchanged.
        """
        thresholds = {
            AVG_SBP: {0: (0, 125), 1: (125, 130), 2: (130, 135), 3: (135, 300)},
            AVG_DBP: {0: (0, 80), 2: (80, 90), 3: (90, 200)},
            PEAK_SBP: 165,
            LOW_SBP: 90,
        }

        status_message = (
            {0: "Optimal", 1: "Within Target - Minor Adjustment", 2: "Out of Target - Moderate Intervention", 3: "Out of Target - Aggressive Intervention"}
            if not hide_intervention
            else {0: "Optimal", 1: "Within Target", 2: "Out of Target", 3: "Out of Target"}
        )

        if self.metadata is None:
            self.calculate_aggregated_metadata()

        latest_tf_key = next(
            (k for k in self.metadata if "Current" in k or "Latest" in k), None
        )
        latest_tf = self.metadata[latest_tf_key]

        avg_sbp = round(latest_tf[AVG_SBP], 1)
        avg_dbp = round(latest_tf[AVG_DBP], 1)
        peak_sbp = round(latest_tf[PEAK_SBP], 1)
        low_sbp = round(latest_tf[LOW_SBP], 1)

        forms_manager = HealthieForms()
        lookup_manager = LookUpCodesManagement()
        entry = lookup_manager.retrieve_entry_by_internal_key(self.syntrillo_internal_key)

        form_id, symptomatic_bp_module_id = self.syntrillo_database_manager.get_form_module_ids_by_module_label("symptomatic_bp")
        _, bp_alert_type_module_id = self.syntrillo_database_manager.get_form_module_ids_by_module_label("bp_alert_type")
        _, bp_alert_date_module_id = self.syntrillo_database_manager.get_form_module_ids_by_module_label("bp_alert_date")

        response = forms_manager.get_form_answers(
            custom_module_form_id=form_id,
            user_id=entry["healthie_user_id"],
        )

        active_timeframe = self.timeframed_data.get("Current") or self.timeframed_data.get("Latest")
        timeframe_start_date = active_timeframe[1][TIMESTAMP_LOCAL].min() if active_timeframe else None

        symptomatic_hypotension_count = 0
        if response and "formAnswerGroups" in response and timeframe_start_date:
            for group in response["formAnswerGroups"]:
                try:
                    answers = {a["custom_module_id"]: a["answer"] for a in group.get("form_answers", [])}
                    if (
                        answers.get(symptomatic_bp_module_id) == "Yes"
                        and answers.get(bp_alert_type_module_id) == "Hypotension"
                        and answers.get(bp_alert_date_module_id)
                    ):
                        bp_alert_date = None
                        raw = answers[bp_alert_date_module_id]
                        try:
                            bp_alert_date = datetime.fromisoformat(raw.split("T")[0])
                        except (ValueError, AttributeError):
                            try:
                                bp_alert_date = datetime.strptime(raw, "%Y-%m-%d")
                            except (ValueError, TypeError):
                                pass
                        if bp_alert_date and pd.notna(timeframe_start_date):
                            if bp_alert_date >= timeframe_start_date.replace(tzinfo=None):
                                symptomatic_hypotension_count += 1
                except Exception as e:
                    logger.error(f"Error parsing symptomatic hypotension data: {e}")

        near_hypotensive_count = 0
        if active_timeframe:
            df = active_timeframe[1]
            near_hypotensive_count = len(df[(df[SYSTOLIC] > 90) & (df[SYSTOLIC] <= 95)])

        data = {
            "date_range": active_timeframe[0] if active_timeframe else None,
            "status": {"value": "", "grade": ""},
            "avg_sbp": {"value": avg_sbp, "grade": ""},
            "avg_dbp": {"value": avg_dbp, "grade": ""},
            "peak_sbp": {"value": peak_sbp, "grade": ""},
            "low_sbp": {"value": low_sbp, "grade": ""},
            "symptomatic_hypotension": {
                "value": symptomatic_hypotension_count,
                "grade": 3 if symptomatic_hypotension_count > 0 else 0,
            },
            "near_hypotensive": {
                "value": near_hypotensive_count,
                "grade": 2 if near_hypotensive_count > 0 else 0,
            },
        }

        for grade, (low, high) in thresholds[AVG_SBP].items():
            if low <= avg_sbp < high:
                data["avg_sbp"]["grade"] = grade
                break

        for grade, (low, high) in thresholds[AVG_DBP].items():
            if low <= avg_dbp < high:
                data["avg_dbp"]["grade"] = grade
                break

        data["peak_sbp"]["grade"] = 3 if peak_sbp >= thresholds[PEAK_SBP] else 0
        data["low_sbp"]["grade"] = 3 if low_sbp < thresholds[LOW_SBP] else 0

        data["status"]["grade"] = max(
            data["avg_sbp"]["grade"],
            data["avg_dbp"]["grade"],
            data["peak_sbp"]["grade"],
            data["low_sbp"]["grade"],
            data["symptomatic_hypotension"]["grade"],
        )
        data["status"]["value"] = status_message[data["status"]["grade"]]

        return data

    # ── Analysis table (React-ready) ─────────────────────────────────────────

    def get_analysis_data(self) -> dict:
        """
        Return a structured analysis dict ready for JSON serialisation.

        Replaces get_analysis_table() which returned a pandas DataFrame.

        Shape:
        {
            "timeframes": [
                {"name": "Baseline", "date_range": "1/1/25 - 1/15/25"},
                ...
            ],
            "rows": [
                {
                    "metric": "Avg SBP (mmHg)",
                    "values": {
                        "Baseline": {"value": 145.2, "grade": 2},
                        "Current":  {"value": 132.1, "grade": 1},
                    },
                    "progress": {
                        "since_baseline": {"delta_pts": 2, "direction": "improving"},
                        "since_prior":    {"delta_pts": 2, "direction": "improving"},
                    }
                },
                ...
            ],
            "overall_progress": {
                "since_baseline": {"delta_pts": 4, "direction": "improving"},
                "since_prior":    {"delta_pts": 2, "direction": "improving"},
            }
        }
        """
        if self.metadata is None:
            self.calculate_aggregated_metadata()

        progress = self._calculate_progress_data()

        timeframe_list = [
            {"name": name, "date_range": date_range}
            for name, (date_range, _) in self.timeframed_data.items()
        ]
        tf_names = [t["name"] for t in timeframe_list]

        rows = []
        for metric in self._ANALYSIS_METRICS:
            display_name = self._METRIC_DISPLAY_NAMES.get(metric, metric)
            metric_progress = progress["per_metric"].get(metric, {})

            values = {}
            for tf_name in tf_names:
                value = self.metadata.get(tf_name, {}).get(metric)
                values[tf_name] = {
                    "value": value,
                    "grade": self._grade_metric(metric, value),
                }

            rows.append({
                "metric": display_name,
                "values": values,
                "progress": {
                    "since_baseline": metric_progress.get("since_baseline"),
                    "since_prior": metric_progress.get("since_prior"),
                },
            })

        return {
            "timeframes": timeframe_list,
            "rows": rows,
            "overall_progress": progress.get("overall", {}),
        }

    # ── Extremes (React-ready) ────────────────────────────────────────────────

    def get_extremes(self) -> list:
        """
        Return extreme blood pressure readings as a list of dicts, newest first.

        Replaces calculate_extremes() which returned a pandas DataFrame.

        Each item:
            {"timestamp": "1/15/25, 8:30 AM", "systolic": 175.0, "diastolic": 95.0}
        """
        if self.bpm_df is None:
            raise RuntimeError("Call get_blood_pressure_dataframe() before get_extremes().")

        df = self.bpm_df
        extremes = df[
            (df[SYSTOLIC] < 90) |
            (df[SYSTOLIC] > 170) |
            (df[DIASTOLIC] > 110)
        ].copy()

        if extremes.empty:
            return []

        logger.info(f"extremes[TIMESTAMP_LOCAL] BEFORE conversion: {extremes[TIMESTAMP_LOCAL]}")

        extremes[TIMESTAMP_LOCAL] = pd.to_datetime(extremes[TIMESTAMP_LOCAL], errors="coerce", utc=True)
        extremes[TIMESTAMP_LOCAL] = (
            extremes[TIMESTAMP_LOCAL]
            .dt.tz_convert("America/New_York")
            .dt.strftime("%-m/%-d/%y, %-I:%M %p")
        )

        logger.info(f"extremes[TIMESTAMP_LOCAL] AFTER conversion: {extremes[TIMESTAMP_LOCAL]}")

        return [
            {
                "timestamp": row[TIMESTAMP_LOCAL],
                "systolic": row[SYSTOLIC],
                "diastolic": row[DIASTOLIC],
            }
            for _, row in extremes[::-1].iterrows()
        ]

    # ── Private helpers ───────────────────────────────────────────────────────

    def _calculate_progress_data(self) -> dict:
        """
        Compute per-metric and overall progress across timeframes.

        Mirrors the legacy calculate_progress() logic but returns structured
        numeric dicts instead of string symbols (+2 / -2 / = / "").

        Returns:
        {
            "per_metric": {
                "<metric_key>": {
                    "since_prior":    {"delta_pts": int, "direction": str} | None,
                    "since_baseline": {"delta_pts": int, "direction": str} | None,
                },
                ...
            },
            "overall": {
                "since_prior":    {"delta_pts": int, "direction": str},
                "since_baseline": {"delta_pts": int, "direction": str},
            }
        }
        """
        timeframes = self.timeframed_data

        current_tf = next((k for k in timeframes if "Current" in k or "Latest" in k), None)
        prior_tf = next((k for k in timeframes if "Prior" in k), None)
        baseline_tf = next((k for k in timeframes if "Baseline" in k), None)

        if not current_tf:
            return {"per_metric": {}, "overall": {}}

        prior_delta = 0
        baseline_delta = 0
        per_metric: dict = {}

        for metric, cfg in self._PROGRESS_METRICS.items():
            current_val = self.metadata.get(current_tf, {}).get(metric)
            prior_val = self.metadata.get(prior_tf, {}).get(metric) if prior_tf else None
            baseline_val = self.metadata.get(baseline_tf, {}).get(metric) if baseline_tf else None

            valid_prior = prior_val is not None and isinstance(prior_val, (int, float))
            valid_baseline = baseline_val is not None and isinstance(baseline_val, (int, float))

            metric_progress: dict = {"since_prior": None, "since_baseline": None}

            if current_val is None:
                per_metric[metric] = metric_progress
                continue

            boundary = cfg["boundary"]

            # Avg SBP / Avg DBP: direction-based scoring
            if metric in (AVG_SBP, AVG_DBP):
                if valid_prior:
                    delta = current_val - prior_val
                    if any(v > boundary for v in [prior_val, current_val]):
                        if delta > 0:
                            prior_delta -= cfg["points"]
                            metric_progress["since_prior"] = {"delta_pts": -cfg["points"], "direction": "worsening"}
                        elif delta < 0:
                            prior_delta += cfg["points"]
                            metric_progress["since_prior"] = {"delta_pts": cfg["points"], "direction": "improving"}
                        else:
                            metric_progress["since_prior"] = {"delta_pts": 0, "direction": "same"}
                    else:
                        metric_progress["since_prior"] = {"delta_pts": 0, "direction": "same"}

                if valid_baseline:
                    delta = current_val - baseline_val
                    if any(v > boundary for v in [baseline_val, current_val]):
                        if delta > 0:
                            baseline_delta -= cfg["points"]
                            metric_progress["since_baseline"] = {"delta_pts": -cfg["points"], "direction": "worsening"}
                        elif delta < 0:
                            baseline_delta += cfg["points"]
                            metric_progress["since_baseline"] = {"delta_pts": cfg["points"], "direction": "improving"}
                        else:
                            metric_progress["since_baseline"] = {"delta_pts": 0, "direction": "same"}
                    else:
                        metric_progress["since_baseline"] = {"delta_pts": 0, "direction": "same"}

            # Peak SBP / Peak DBP: threshold-crossing scoring
            elif metric in (PEAK_SBP, PEAK_DBP):
                high_threshold = cfg["threshold"]

                if valid_prior:
                    if any(v > boundary for v in [prior_val, current_val]):
                        if prior_val < high_threshold <= current_val:
                            prior_delta -= cfg["points"]
                            metric_progress["since_prior"] = {"delta_pts": -cfg["points"], "direction": "worsening"}
                        elif prior_val >= high_threshold > current_val:
                            prior_delta += cfg["points"]
                            metric_progress["since_prior"] = {"delta_pts": cfg["points"], "direction": "improving"}
                        else:
                            metric_progress["since_prior"] = {"delta_pts": 0, "direction": "same"}
                    else:
                        metric_progress["since_prior"] = {"delta_pts": 0, "direction": "same"}

                if valid_baseline:
                    if any(v > boundary for v in [baseline_val, current_val]):
                        if baseline_val < high_threshold <= current_val:
                            baseline_delta -= cfg["points"]
                            metric_progress["since_baseline"] = {"delta_pts": -cfg["points"], "direction": "worsening"}
                        elif baseline_val >= high_threshold > current_val:
                            baseline_delta += cfg["points"]
                            metric_progress["since_baseline"] = {"delta_pts": cfg["points"], "direction": "improving"}
                        else:
                            metric_progress["since_baseline"] = {"delta_pts": 0, "direction": "same"}
                    else:
                        metric_progress["since_baseline"] = {"delta_pts": 0, "direction": "same"}

            per_metric[metric] = metric_progress

        def _to_summary(delta: int) -> dict:
            return {
                "delta_pts": delta,
                "direction": "improving" if delta > 0 else "worsening" if delta < 0 else "same",
            }

        overall: dict = {}
        if prior_tf:
            overall["since_prior"] = _to_summary(prior_delta)
        if baseline_tf:
            overall["since_baseline"] = _to_summary(baseline_delta)

        return {"per_metric": per_metric, "overall": overall}

    @staticmethod
    def _grade_metric(metric: str, value) -> Optional[int]:
        """
        Return 0 (optimal), 1 (caution), 2 (critical), or None (ungraded).

        Mirrors the colour-coding logic from the legacy style_row() method so
        that the React frontend can map grade → colour without reimplementing
        the thresholds.
        """
        if value is None or not isinstance(value, (int, float)):
            return None

        if metric == AVG_SBP:
            if value < 130: return 0
            if value < 140: return 1
            return 2

        if metric == AVG_DBP:
            if value < 80: return 0
            if value < 90: return 1
            return 2

        if metric == SBP_SD:
            if value < 7.5: return 0
            if value < 15:  return 1
            return 2

        if metric == DBP_SD:
            if value < 5:    return 0
            if value < 11.5: return 1
            return 2

        if metric == PEAK_SBP:
            return 0 if value < 170 else 2

        if metric == PEAK_DBP:
            return 0 if value < 110 else 2

        if metric == LOW_SBP:
            return 2 if value < 90 else 0

        if metric in (SBP_COUNT_170, HYPOTENSIVE_COUNT):
            return 2 if value > 0 else 0

        return None  # MEASUREMENT_COUNT, AVG_PP, LOW_DBP, ENGAGEMENT — no colour coding