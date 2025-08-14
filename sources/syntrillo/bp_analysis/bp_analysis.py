import uuid
import pandas as pd
from datetime import datetime, timezone
from typing import Tuple
import textwrap
import io
import re
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import pandas as pd
import plotly.io as pio
import plotly.graph_objects as go
from plotly.subplots import make_subplots

matplotlib.use('Agg')

from syntrillo.remote_monitoring.syntrillo_database_manager import SyntrilloDatabaseManager
from syntrillo.api_tenovi.device_types import DeviceTypes
from syntrillo.api_tenovi.device_measurements import DeviceMeasurements
from syntrillo.bp_analysis.constants import (
    DATE_RANGE,
    MEASUREMENT_COUNT,
    AVG_SBP,
    AVG_DBP,
    PEAK_SBP,
    PEAK_DBP,
    LOW_SBP,
    LOW_DBP,
    SBP_SD,
    DBP_SD,
    SBP_CV,
    DBP_CV,
    SBP_COUNT_170,
    SBP_COUNT_175,
    HYPOTENSIVE_COUNT,
    SYSTOLIC,
    DIASTOLIC,
    TIMESTAMP_LOCAL,
)
from syntrillo.system.logger import logger

class BloodPressureAnalysis:
    """

    Handle patient level blood pressure analysis. Class methods include:
        1. __init__()
            - sets PHI database connection
        2. initialize_data()
            - streamlines method calls (3-6)
        3. get_blood_pressure_dataframe()
            - retrieves tenovi BP values; sets bpm_df and returns bpm_df
        4. calculate_metadata()
            - returns dict containing total values since baseline for analysis rows; used for calculate_since_baseline()
        5. calculate_timeframes()
            - returns new bpm_df sorted by timeframes; used for calculate_analysis()
        6. calculate_analysis()
            - returns analysis dataframe table with progress rows
        7. calculate_progress()
            - attaches progress cells to analysis dataframe; used in calculate_analysis
        8. calculate_since_baseline()
            - returns updated analysis dataframe with 3 additional columns; redacted
        9. calculate_extremes()
            - returns extremes dataframe
        10. style_row()
            - styles df rows depending on metric and value
        11. save_to_pdf()
            - returns pdf that combines analysis df and extremes df

    """

    # Class variables
    syntrillo_internal_key : uuid.UUID = None
    syntrillo_database_manager : SyntrilloDatabaseManager = None
    bpm_df : pd.DataFrame = None
    analysis_df : pd.DataFrame = None
    timeframed_data : dict = None
    HYPERTENSION_SBP_THRESHOLD = 170
    HYPERTENSION_DBP_THRESHOLD = 110
    HYPOTENSION_SBP_THRESHOLD = 95


    def __init__(self, syntrillo_internal_key : uuid.UUID = None) -> None:
        self.syntrillo_internal_key = syntrillo_internal_key
        self.syntrillo_database_manager = SyntrilloDatabaseManager(syntrillo_internal_key) # set up PHI database connection for this user


    def initialize_data(self) -> None:
        # Get all available blood pressure data
        _, _ = self.get_blood_pressure_dataframe(start_date=None, end_date=None)

        # Generate analysis + extremes table using BloodPressureAnalysis class methods
        self.calculate_metadata() # Used to calculate since baseline columns; calculates row values since baseline
        self.calculate_timeframes() # Sorts and separates data by Baseline, Prior, & Current, in two week increments
        self.calculate_analysis() # Calculates row values for each timeframe

        if self.analysis_df is not None:
            return True
        else:
            return False


    def get_blood_pressure_dataframe(
        self,
        start_date : datetime = None,
        end_date : datetime = None,
        ) -> Tuple[pd.DataFrame, dict]:
        """
        Get BPM report, only Blood Pressure data.

        https://tenovi.com/hwi-device-overview/#tenovi-bpm

        https://tenovi.com/bpm/

        Available metrics:
          - blood_pressure : value_1 is systolic, value_2 is diastolic  mmHg

        Returns a tuple:
            - pandas dataframe with columns:
                - timestamp_local: local time to the patient, string type, using datetime isoformat (to prevent any databasing and conversion issue)
                - systolic
                - diastolic
            - log : dict with success and error message

        """

        # ------------------------------------------------------
        # get data
        #   - make sure start_date and end_date are at midnight
        #   - deal with edges cases


        # ---
        # deal with None start_date, end_date
        if start_date is None:
            first_record, log = self.syntrillo_database_manager.get_first_tenovi_device_data(device_name=DeviceTypes.TENOVI_DEVICE_NAME__BPM_PREFIX)
            if first_record is not None:
                start_date = datetime.strptime(first_record['timestamp_local'], '%Y-%m-%dT%H:%M:%S.%f%z')
            else:
                start_date = datetime(2000, 1, 1)
        if end_date is None:
            end_date = datetime.now()

        # ---
        # the time of start_date should be 00:00:00
        start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)

        # the time of end_date should be 23:59:59
        end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=0)

        # ---
        # end_date - start date < 2 days, return an error
        tz_utc = timezone.utc # quick fix if one date has no timezone to allow the substraction
        if (end_date.astimezone(tz_utc) - start_date.astimezone(tz_utc)).days < 2:
            log = {
                'success': False,
                'error': 'Report period is too short',
            }
            return None, log

        # ---
        # get data from PHI database, ordered by timestamp
        bpm_df, log = self.syntrillo_database_manager.get_tenovi_device_metric_data(
            metric_name=DeviceMeasurements.TENOVI_METRICS_BPM_BLOOD_PRESSURE,
            start_date=start_date,
            end_date=end_date,
        )

        # ---
        # exit if no data : None or empty dataframe
        if bpm_df is None or bpm_df.empty or log['success'] == False:
            overall_log = {
                'success': False,
                'error': 'No blood pressure data found.',
                'log': log,
            }
            return None, overall_log

        # ---
        # rename columns :
        #  - value_1 -> systolic
        #  - value_2 -> diastolic
        # drop 'device_name' and 'metric_name' columns
        bpm_df = bpm_df.rename(columns={'value_1': 'systolic', 'value_2': 'diastolic'})
        bpm_df = bpm_df.drop(columns=['device_name', 'metric_name'])

        # ---
        # make sure systolic and diastolic are numeric
        bpm_df['systolic'] = pd.to_numeric(bpm_df['systolic'], errors='coerce')
        bpm_df['diastolic'] = pd.to_numeric(bpm_df['diastolic'], errors='coerce')

        # ---

        # store the dataframe in the class
        self.bpm_df = bpm_df

        # return the dataframe and the log
        return bpm_df, log

    def calculate_timeframes(self) -> dict:
        """
        Extracts bpm_df values into Baseline (first 2 weeks), Prior (2 weeks before Current), and Current (latest 2 weeks).
        Dynamically includes only relevant timeframes based on total available data.
        Ensures a minimum of 3 measurements per timeframe and at least one non-null measurement for it to be included.

        Returns:
            dict: {
                "Baseline": (date_range, dataframe),
                "Prior": (date_range, dataframe),
                "Current": (date_range, dataframe)
            }
        """
        df = self.bpm_df

        # Ensure timestamp_local is datetime
        # df['timestamp_local'] = pd.to_datetime(df['timestamp_local'], errors='coerce')

        latest_date = df['timestamp_local'].max()
        baseline_start = df['timestamp_local'].min()

        # Calculate total elapsed time in weeks
        total_weeks = (latest_date - baseline_start).days / 7

        # Define time ranges
        current_start = latest_date - pd.Timedelta(weeks=2)
        baseline_end = baseline_start + pd.Timedelta(weeks=2)
        prior_end = current_start - pd.Timedelta(days=1)
        prior_start = prior_end - pd.Timedelta(weeks=2)

        # Minimum number of required measurements
        min_measurements = 3

        # Initialize timeframes in correct order
        timeframes = {}

        def is_valid_timeframe(timeframe_df):
            """Check if a timeframe has at least one valid (non-null) measurement and meets the min count."""
            return len(timeframe_df.dropna()) >= min_measurements and timeframe_df.notna().any().any()

        # Include Baseline first if at least 4 weeks of data and it has enough measurements
        baseline_df = df[(df['timestamp_local'] >= baseline_start) & (df['timestamp_local'] < baseline_end)]
        if total_weeks >= 4 and is_valid_timeframe(baseline_df):
            # timeframes[f"Baseline ({baseline_start.strftime('%-m/%-d/%y')}-{baseline_end.strftime('%-m/%-d/%y')})"] = baseline_df
            timeframes[f"Baseline"] = (f"{baseline_start.strftime('%-m/%-d/%y')} - {baseline_end.strftime('%-m/%-d/%y')}", baseline_df)

        # Include Prior in the middle if at least 6 weeks of data and it has enough measurements
        prior_df = df[(df['timestamp_local'] >= prior_start) & (df['timestamp_local'] < prior_end)]
        if total_weeks >= 5 and is_valid_timeframe(prior_df):
            # timeframes[f"Prior ({prior_start.strftime('%-m/%-d/%y')}-{prior_end.strftime('%-m/%-d/%y')})"] = prior_df
            timeframes[f"Prior"] = (f"{prior_start.strftime('%-m/%-d/%y')} - {prior_end.strftime('%-m/%-d/%y')}", prior_df)

        # Always include Current last, but only if it has enough measurements
        current_df = df[df['timestamp_local'] >= current_start]
        if is_valid_timeframe(current_df):
            # Determine if latest_date is within 3 days of today
            today = datetime.now().date()
            if isinstance(latest_date, pd.Timestamp):
                latest_date_only = latest_date.date()
            else:
                latest_date_only = latest_date
            # 'Current' if most recent measurement is within 5 days of today, 'Latest' if not
            if (today - latest_date_only).days <= 5:
                last_timeframe_name = "Current"
            else:
                last_timeframe_name = "Latest"
            timeframes[f"{last_timeframe_name}"] = (f"{current_start.strftime('%-m/%-d/%y')} - {latest_date.strftime('%-m/%-d/%y')}", current_df)

        self.timeframed_data = timeframes

        # print(f"---- Timeframed Data ----- {timeframes}")
        return timeframes

    def calculate_metadata(self, date_range, df) -> dict:
        """Calculate blood pressure analysis metadata from dataframe."""

        # Initialize default data structure
        data = {
            'Date Range': date_range,
            'Measurement Count': 0,
            'Avg SBP (mmHg)': None,
            'Avg DBP (mmHg)': None,
            'Peak SBP² (mmHg)': None,
            'Peak DBP² (mmHg)': None,
            'Low SBP³ (mmHg)': None,
            'Low DBP³ (mmHg)': None,
            'SBP SD (mmHg)': None,
            'DBP SD (mmHg)': None,
            'SBP CV (%)': None,
            'DBP CV (%)': None,
            # 'SBP Count (>= 160)': 0,
            # 'SBP Count (>= 165)': 0,
            'SBP Count (>= 170)': 0,
            'SBP Count (>= 175)': 0,
            # 'SBP Count (<=80)': 0,
            # 'SBP Count (<=85)': 0,
            # 'SBP Count (<=90)': 0,
            # 'SBP Count (<=95)': 0,
            'Hypotensive Count⁴': 0,
        }

        if df.empty:
            return data

        # Set values directly in the data dictionary
        data['Measurement Count'] = len(df)
        data['Avg SBP (mmHg)'] = round(df['systolic'].mean(), 2)
        data['Avg DBP (mmHg)'] = round(df['diastolic'].mean(), 2)
        data['Peak SBP² (mmHg)'] = round(df['systolic'].nlargest(3).mean(), 2)
        data['Peak DBP² (mmHg)'] = round(df['diastolic'].nlargest(3).mean(), 2)
        data['Low SBP³ (mmHg)'] = round(df['systolic'].min(), 2)
        data['Low DBP³ (mmHg)'] = round(df['diastolic'].min(), 2)
        data['SBP SD (mmHg)'] = round(df['systolic'].std(), 2)
        data['DBP SD (mmHg)'] = round(df['diastolic'].std(), 2)

        # Calculate coefficients of variation
        systolic_sd = data['SBP SD (mmHg)']
        diastolic_sd = data['DBP SD (mmHg)']
        avg_systolic = data['Avg SBP (mmHg)']
        avg_diastolic = data['Avg DBP (mmHg)']

        data['SBP CV (%)'] = round((systolic_sd / avg_systolic) * 100, 2) if avg_systolic else None
        data['DBP CV (%)'] = round((diastolic_sd / avg_diastolic) * 100, 2) if avg_diastolic else None

        # Calculate threshold counts
        # data['SBP Count (>= 160)'] = len(df[df['systolic'] >= 160])
        # data['SBP Count (>= 165)'] = len(df[df['systolic'] >= 165])
        data['SBP Count (>= 170)'] = len(df[df['systolic'] >= 170])
        data['SBP Count (>= 175)'] = len(df[df['systolic'] >= 175])
        # data['SBP Count (<=80)'] = len(df[df['systolic'] <= 80])
        # data['SBP Count (<=85)'] = len(df[df['systolic'] <= 85])
        # data['SBP Count (<=90)'] = len(df[df['systolic'] <= 90])
        # data['SBP Count (<=95)'] = len(df[df['systolic'] <= 95])
        data['Hypotensive Count⁴'] = len(df[df['systolic'] <= self.HYPOTENSION_SBP_THRESHOLD + 5])

        return data

    def calculate_metadata_v2(self, df: pd.DataFrame, date_range: str = None) -> dict:
        """
        Calculate blood pressure analysis metadata from dataframe.

        Args:
            df (pd.DataFrame): The dataframe to calculate the metadata from
            date_range (str): The date range of the dataframe

        Returns:
            dict: The metadata
        """

        # Initialize default data structure
        data = {
            DATE_RANGE: date_range,
            MEASUREMENT_COUNT: 0,
            AVG_SBP: None,
            AVG_DBP: None,
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

        # Set values directly in the data dictionary
        data[MEASUREMENT_COUNT] = len(df)
        data[AVG_SBP] = round(df[SYSTOLIC].mean(), 2)
        data[AVG_DBP] = round(df[DIASTOLIC].mean(), 2)
        data[PEAK_SBP] = round(df[SYSTOLIC].nlargest(3).mean(), 2)
        data[PEAK_DBP] = round(df[DIASTOLIC].nlargest(3).mean(), 2)
        data[LOW_SBP] = round(df[SYSTOLIC].min(), 2)
        data[LOW_DBP] = round(df[DIASTOLIC].min(), 2)
        data[SBP_SD] = round(df[SYSTOLIC].std(), 2)
        data[DBP_SD] = round(df[DIASTOLIC].std(), 2)

        # Calculate coefficients of variation
        data[SBP_CV] = round((data[SBP_SD] / data[AVG_SBP]) * 100, 2) if data[AVG_SBP] else None
        data[DBP_CV] = round((data[DBP_SD] / data[AVG_DBP]) * 100, 2) if data[AVG_DBP] else None

        # Calculate threshold counts
        data[SBP_COUNT_170] = len(df[df[SYSTOLIC] >= 170])
        data[SBP_COUNT_175] = len(df[df[SYSTOLIC] >= 175])
        data[HYPOTENSIVE_COUNT] = len(df[df[SYSTOLIC] <= self.HYPOTENSION_SBP_THRESHOLD + 5])

        return data

    def get_analysis_table(self) -> pd.DataFrame:
        """

        Creates analysis dataframe using self.timeframed_data. Each column is a timeframe.

        Rows below:
            - Avg SBP
            - Avg DBP
            - Peak SBP (avg of 3 highest values)
            - Peak DBP
            - Low SBP (single lowest)
            - Low DBP
            - SBP SD (standard deviation)
            - DBP SD
            - SBP CV (coefficient of variation)
            - DBP CV
            - SBP Count >= 170
            - SBP Count >= 175
            - Hypotensive Count (low SBP)

        Appends three additional rows regarding progress and timeframe grading:
            - "Progress (pts)" (current vs. prior)
            - "Baseline Progress (pts)" (current vs. baseline)
            - Overall
            * Should be separated out in different class method?

        """
        timeframes = self.timeframed_data

        analysis = {}

        for name, (date_range, frame) in timeframes.items():
            analysis[name] = self.calculate_metadata(date_range=date_range, df=frame)

        analysis_with_progress = self.calculate_progress(analysis=analysis, timeframed_data=timeframes)
        df = pd.DataFrame.from_dict(analysis_with_progress, orient='index').T

        columns_to_update = [
            col for col in df.columns
            if not col.startswith("Since")
        ]

        df.loc['Overall', columns_to_update] = df[columns_to_update].apply(self.calculate_overall, axis=0)
        df.loc['Overall'] = df.loc['Overall'].fillna("")

        # Set class variable
        self.analysis_df = df

        return df

    @staticmethod
    def calculate_progress(analysis: dict, timeframed_data: dict) -> dict:
        """
        Calculates progress based on timeframed data.
        Adjusts dynamically based on available timeframes (Baseline, Prior, Current).
        """

        # Define point system and thresholds
        points = {
            'Avg SBP (mmHg)': 2,
            'Avg DBP (mmHg)': 2,
            'SBP CV (%)': 1,
            'DBP CV (%)': 1,
            'SBP SD (mmHg)': 1,
            'DBP SD (mmHg)': 1,
            'Peak SBP² (mmHg)': 2,
            'Peak DBP² (mmHg)': 2
        }

        thresholds = {
            'Avg SBP (mmHg)': 2,
            'Avg DBP (mmHg)': 2,
            'SBP CV (%)': 1.1,
            'DBP CV (%)': 1.4,
            'SBP SD (mmHg)': 1.5,
            'DBP SD (mmHg)': 1.3,
            'Peak SBP² (mmHg)': 170,
            'Peak DBP² (mmHg)': 110
        }

        boundaries = {
            'Avg SBP (mmHg)': [0, 130],
            'Avg DBP (mmHg)': [0, 80],
            'SBP CV (%)': [0, 5.5],
            'DBP CV (%)': [0, 6],
            'SBP SD (mmHg)': [0, 7.5],
            'DBP SD (mmHg)': [0, 5],
            'Peak SBP² (mmHg)': [0, 170],
            'Peak DBP² (mmHg)': [0, 110]
        }

        prior_delta = 0
        baseline_delta = 0

        # Extract available timeframes
        current_timeframe = next((key for key in timeframed_data if "Current" in key or "Latest" in key), None)
        prior_timeframe = next((key for key in timeframed_data if "Prior" in key), None)
        baseline_timeframe = next((key for key in timeframed_data if "Baseline" in key), None)

        if not current_timeframe:
            return analysis  # No current timeframe means no comparison can be made

        # Initialize the progress tracking
        all_metrics = list(next(iter(analysis.values())).keys())
        if baseline_timeframe:
            analysis['Since Baseline¹'] = {metric: ("" if metric not in points else "=") for metric in all_metrics}

        if prior_timeframe:
            analysis['Since Prior¹'] = {metric: ("" if metric not in points else "=") for metric in all_metrics}

        # print(f"------------------- {analysis}")

        for metric in analysis[current_timeframe]:

            current_value = analysis[current_timeframe][metric]
            prior_value = analysis.get(prior_timeframe, {}).get(metric, None)
            baseline_value = analysis.get(baseline_timeframe, {}).get(metric, None)

            # print(f"{metric}: {type(current_value)}")

            # Ensure values are valid for comparison
            valid_prior = prior_value is not None and isinstance(prior_value, (int, float))
            valid_baseline = baseline_value is not None and isinstance(baseline_value, (int, float))

            if current_value is not None:
                prior_unit_change = current_value - prior_value if valid_prior else None
                prior_percent_change = (prior_unit_change / prior_value * 100) if valid_prior and prior_value != 0 else None
                valid_prior_change = prior_unit_change is not None and prior_percent_change is not None

                baseline_unit_change = current_value - baseline_value if valid_baseline else None
                baseline_percent_change = (baseline_unit_change / baseline_value * 100) if valid_baseline and baseline_value != 0 else None
                valid_baseline_change = baseline_unit_change is not None and baseline_percent_change is not None

                # Default progress symbols
                prior_progress = ""
                base_progress = ""

                # Skip metrics without thresholds
                # if metric not in thresholds.keys():
                #     continue

                # Handle Avg SBP and DBP
                if metric in ['Avg SBP (mmHg)', 'Avg DBP (mmHg)']:
                    if valid_prior and any(val > boundaries[metric][1] for val in [prior_value, current_value]):
                        if prior_unit_change > 0:
                            prior_delta -= points[metric]
                            prior_progress = "-2"
                        elif prior_unit_change < 0:
                            prior_delta += points[metric]
                            prior_progress = "+2"

                    if valid_baseline and any(val > boundaries[metric][1] for val in [baseline_value, current_value]):
                        if baseline_unit_change > 0:
                            baseline_delta -= points[metric]
                            base_progress = "-2"
                        elif baseline_unit_change < 0:
                            baseline_delta += points[metric]
                            base_progress = "+2"

                    # print(f"Baseline Delta (after Avg): {baseline_delta}")

                # Handle SBP-SD and DBP-SD
                elif metric in ['SBP SD (mmHg)', 'DBP SD (mmHg)']:
                    if valid_prior and valid_prior_change:
                        if abs(prior_unit_change) >= thresholds[metric] and any(val > boundaries[metric][1] for val in [prior_value, current_value]):
                            if prior_unit_change > 0:
                                prior_delta -= points[metric]
                                prior_progress = "-1"
                            elif prior_unit_change < 0:
                                prior_delta += points[metric]
                                prior_progress = "+1"

                    if valid_baseline and valid_baseline_change:
                        if abs(baseline_unit_change) >= thresholds[metric] and any(val > boundaries[metric][1] for val in [baseline_value, current_value]):
                            if baseline_unit_change > 0:
                                baseline_delta -= points[metric]
                                base_progress = "-1"
                            elif baseline_unit_change < 0:
                                baseline_delta += points[metric]
                                base_progress = "+1"

                    # print(f"Baseline Delta (after SD): {baseline_delta}")

                # Handle SBP-CV and DBP-CV
                elif metric in ['SBP CV (%)', 'DBP CV (%)']:
                    if valid_prior and valid_prior_change:
                        if abs(prior_percent_change) >= thresholds[metric] and any(val > boundaries[metric][1] for val in [prior_value, current_value]):
                            if prior_percent_change > 0:
                                prior_delta -= points[metric]
                                prior_progress = "-1"
                            elif prior_percent_change < 0:
                                prior_delta += points[metric]
                                prior_progress = "+1"

                    if valid_baseline and valid_baseline_change:
                        if abs(baseline_percent_change) >= thresholds[metric] and any(val > boundaries[metric][1] for val in [baseline_value, current_value]):
                            if baseline_percent_change > 0:
                                baseline_delta -= points[metric]
                                base_progress = "-1"
                            elif baseline_percent_change < 0:
                                baseline_delta += points[metric]
                                base_progress = "+1"

                    # print(f"Baseline Delta (after CV): {baseline_delta}")

                # Handle Peak SBP/DBP
                elif metric.startswith('Peak'):
                    high_threshold = thresholds[metric]
                    if valid_prior and any(val > boundaries[metric][1] for val in [prior_value, current_value]):
                        if prior_value < high_threshold < current_value:
                            prior_delta -= points[metric]
                            prior_progress = "-2"
                        elif prior_value > high_threshold >= current_value:
                            prior_delta += points[metric]
                            prior_progress = "+2"

                    if valid_baseline and any(val > boundaries[metric][1] for val in [baseline_value, current_value]):
                        if baseline_value < high_threshold < current_value:
                            baseline_delta -= points[metric]
                            base_progress = "-2"
                        elif baseline_value > high_threshold >= current_value:
                            baseline_delta += points[metric]
                            base_progress = "+2"

                # print(f"Baseline Delta (after Peak): {baseline_delta}")

                # Store progress result
                if valid_baseline:
                    analysis['Since Baseline¹'][metric] = f"{base_progress}"

                if valid_prior:
                    analysis['Since Prior¹'][metric] = f"{prior_progress}"

        # Overall progress
        since_prior_status = "Improving" if prior_delta > 0 else "Worsening" if prior_delta < 0 else "Same"
        since_baseline_status = "Improving" if baseline_delta > 0 else "Worsening" if baseline_delta < 0 else "Same"

        if valid_prior:
            analysis['Since Prior¹']['Progress (pts)'] = f"{since_prior_status} ({prior_delta})"

        if valid_baseline:
            analysis['Since Baseline¹']['Progress (pts)'] = f"{since_baseline_status} ({baseline_delta})"

        # Ensure keys exist in all timeframes
        for tf in [baseline_timeframe, prior_timeframe, current_timeframe]:
            if tf:
                analysis.setdefault(tf, {}).setdefault('Progress (pts)', '-')

        return analysis


    @staticmethod
    def calculate_overall(column):
        """
        Calculate the overall rating for a timeframe based on individual metrics.
        Priority: Poor > Okay > Good
        """
        # Initialize the default rating as 'Good'
        overall_rating = 'Good'

        # Iterate through each metric in the column
        for metric, value in column.items():
            if isinstance(value, str):
                # Remove trend arrows (↑/↓) and convert to numeric
                value = pd.to_numeric(value.replace('+', '').replace('-', '').strip(), errors='coerce')

            if metric == 'Avg SBP (mmHg)' and value is not None:
                if value >= 140:
                    return 'Poor'  # Immediate return for highest priority
                elif 130 <= value < 140:
                    overall_rating = 'Okay'

            elif metric == 'Avg DBP (mmHg)' and value is not None:
                if value >= 90:
                    return 'Poor'
                elif 80 <= value < 90:
                    overall_rating = 'Okay'

            elif metric == 'SBP SD (mmHg)' and value is not None:
                if value >= 15:
                    return 'Poor'
                elif 7.5 <= value < 15:
                    overall_rating = 'Okay'

            elif metric == 'DBP SD (mmHg)' and value is not None:
                if value >= 11.5:
                    return 'Poor'
                elif 5 <= value < 11.5:
                    overall_rating = 'Okay'

            elif metric == 'SBP CV (%)' and value is not None:
                if value >= 11:
                    return 'Poor'
                elif 5.5 <= value < 11:
                    overall_rating = 'Okay'

            elif metric == 'DBP CV (%)' and value is not None:
                if value >= 13:
                    return 'Poor'
                elif 6 <= value < 13:
                    overall_rating = 'Okay'

            elif metric == 'Peak SBP² (mmHg)' and value is not None:
                if value >= 170:
                    return 'Poor'

            elif metric == 'Peak DBP² (mmHg)' and value is not None:
                if value >= 110:
                    return 'Poor'

        # Return the overall rating ('Okay' or 'Good')
        return overall_rating


    def calculate_since_baseline(self, metadata, analysis_table):
        """

        Appends 3 additional columns (unit change, percent change, totals) to analysis df

        """
        def calculate_unit_change(row, baseline_col, current_col):
            baseline_val = pd.to_numeric(str(row[baseline_col]).replace('+', '').replace('-', '').replace('/', '').replace('=', '').strip(), errors='coerce')
            current_val = pd.to_numeric(str(row[current_col]).replace('+', '').replace('-', '').replace('/', '').replace('=', '').strip(), errors='coerce')

            if pd.notna(baseline_val) and pd.notna(current_val):
                numeric_change = round(current_val - baseline_val, 2)
                return numeric_change
            return ''

        def calculate_percent_change(row, baseline_col, current_col):
            baseline_val = pd.to_numeric(str(row[baseline_col]).replace('+', '').replace('-', '').replace('/', '').replace('=', '').strip(), errors='coerce')
            current_val = pd.to_numeric(str(row[current_col]).replace('+', '').replace('-', '').replace('/', '').replace('=', '').strip(), errors='coerce')

            if pd.notna(baseline_val) and pd.notna(current_val):
                if baseline_val == 0:
                    return 100.0 if current_val > 0 else (0.0 if current_val == 0 else -100.0)  # Handles 0 baseline cases
                percent_change = round((current_val - baseline_val) / abs(baseline_val) * 100, 1)
                return percent_change
            return ''


        # Identify the Baseline and Current columns dynamically
        baseline_col = next((col for col in analysis_table.columns if 'Baseline' in col), None)
        current_col = next((col for col in analysis_table.columns if 'Current' in col), None)

        if baseline_col and current_col:
            # Add the "Δ Unit" column from analysis_table, matching index labels
            analysis_table['Since Baseline (Δ Unit)'] = analysis_table.apply(lambda row: calculate_unit_change(row, baseline_col, current_col), axis=1)
            # Add the "Δ Percent" column from analysis_table, matching index labels
            analysis_table['Since Baseline (Δ Percent)'] = analysis_table.apply(lambda row: f"{calculate_percent_change(row, baseline_col, current_col)}%", axis=1)

        # Add the "Total" column from counts_dict, matching index labels
        analysis_table['Since Baseline (Total)'] = analysis_table.index.map(lambda idx: metadata.get(idx, ''))

        return analysis_table


    def calculate_extremes(self):
        """

        Returns df containing only values that lie outside of low and high boundaries

        """
        BLOOD_PRESSURE_LOW = 90
        BLOOD_PRESSURE_HIGH_VALUE1 = 170
        BLOOD_PRESSURE_HIGH_VALUE2 = 110
        df = self.bpm_df
        extremes = df[(df['systolic'] < BLOOD_PRESSURE_LOW) |
                  (df['systolic'] > BLOOD_PRESSURE_HIGH_VALUE1) |
                  (df['diastolic'] > BLOOD_PRESSURE_HIGH_VALUE2)]

        logger.info(f"*** extremes['timestamp_local'] BEFORE conversion: {extremes['timestamp_local']}")

        extremes['timestamp_local'] = pd.to_datetime(extremes['timestamp_local'], errors='coerce', utc=True)
        extremes['timestamp_local'] = extremes['timestamp_local'].dt.tz_convert('America/New_York').dt.strftime('%-m/%-d/%y, %-I:%M %p')

        # extremes['timestamp_local'] = pd.to_datetime(extremes['timestamp_local'], utc=True).dt.strftime('%-m/%d/%y, %I:%M:%S %p')

        logger.info(f"*** extremes['timestamp_local'] AFTER conversion: {extremes['timestamp_local']}")

        extremes.rename(columns={'timestamp_local': 'Timestamp', 'systolic': 'Systolic', 'diastolic': 'Diastolic'}, inplace=True)

        return extremes[['Timestamp', 'Systolic', 'Diastolic']].reset_index(drop=True)[::-1]


    @staticmethod
    def style_row(row):
        """

        Colorizes analysis df.

        """
        if not hasattr(row, 'name'):
            return ['background-color: white; padding: 8px; text-align: center' for _ in row]

        metric = row.name
        styles = []
        for val in row:
            color = 'white'
            if pd.notna(val):

                # Convert val to string and check if it contains "+" or "-"
                if isinstance(val, str) and ("+" in val or "-" in val):
                    styles.append(f'background-color: {color}; padding: 8px')
                    continue

                # Colorize 'Overall' row
                if metric == 'Overall':
                    if val == 'Good':
                        color = 'lightgreen'
                    elif val == 'Okay':
                        color = 'yellow'
                    elif val == 'Poor':
                        color = 'lightcoral'

                # Convert string values to a numeric value
                try:
                    if isinstance(val, str):
                        value_num = pd.to_numeric(val, errors='coerce')
                    else:
                        value_num = val
                except Exception:
                    value_num = None

                if isinstance(value_num, float):
                    # print(f"{value_num} is float")
                    value_num = round(value_num, 1)

                if value_num is not None and not pd.isna(value_num):
                    if metric == 'Avg SBP (mmHg)':
                        if value_num < 130:
                            color = 'lightgreen'
                        elif 130 <= value_num <= 139:
                            color = 'yellow'
                        else:
                            color = 'lightcoral'
                    elif metric == 'Avg DBP (mmHg)':
                        if value_num < 80:
                            color = 'lightgreen'
                        elif 80 <= value_num <= 89:
                            color = 'yellow'
                        else:
                            color = 'lightcoral'
                    elif metric == 'SBP SD (mmHg)':
                        if value_num < 7.5:
                            color = 'lightgreen'
                        elif value_num < 15:
                            color = 'yellow'
                        else:
                            color = 'lightcoral'
                    elif metric == 'DBP SD (mmHg)':
                        if value_num < 5:
                            color = 'lightgreen'
                        elif value_num < 11.5:
                            color = 'yellow'
                        else:
                            color = 'lightcoral'
                    elif metric == 'SBP CV (%)':
                        if value_num < 5.5:
                            color = 'lightgreen'
                        elif value_num < 11:
                            color = 'yellow'
                        else:
                            color = 'lightcoral'
                    elif metric == 'DBP CV (%)':
                        if value_num < 6:
                            color = 'lightgreen'
                        elif value_num < 13:
                            color = 'yellow'
                        else:
                            color = 'lightcoral'
                    elif metric == 'Peak SBP² (mmHg)':
                        if value_num < 170:
                            color = 'lightgreen'
                        else:
                            color = 'lightcoral'
                    elif metric == 'Peak DBP² (mmHg)':
                        if value_num < 110:
                            color = 'lightgreen'
                        else:
                            color = 'lightcoral'
            # Append the style for this cell
            styles.append(f'background-color: {color}; padding: 8px')

        return styles


    @staticmethod
    def wrap_text(text, width=16):
        """Manually inserts line breaks to wrap text in table headers."""
        return "\n".join(textwrap.wrap(text, width))

    @staticmethod
    def save_to_pdf(analysis, extremes, report_title="Report"):
        """
        Saves analysis and extremes tables as a PDF with conditional cell coloring.
        :param analysis: DataFrame containing analysis data
        :param extremes: DataFrame containing extreme values
        :param report_title: Title for the report
        :return: BytesIO buffer containing the PDF
        """
        pdf_buffer = io.BytesIO()  # Create an in-memory buffer

        with PdfPages(pdf_buffer) as pdf:
            wrapped_col_labels = ['Metric'] + list(analysis.columns)

            # Create figure for analysis table
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.axis('off')
            ax.axis('tight')

            # Convert DataFrame to a 2D list for the table
            table_data = analysis.reset_index().values.tolist()

            # Create the table
            table = ax.table(cellText=table_data,
                            colLabels=wrapped_col_labels,
                            cellLoc='center', loc='center')

            table.auto_set_font_size(False)
            table.scale(1.2, 1.2)

            # Regex pattern to detect only `+`, `-`, or `=`
            trend_symbol_pattern = re.compile(r'^[+=/-]+$')

            # Apply cell color logic
            for (row, col), cell in table.get_celld().items():
                if row == 0:  # Header row
                    cell.set_fontsize(8)
                    cell.set_facecolor("lightgray")
                elif col == 0:  # Row labels
                    cell.set_fontsize(8)
                else:  # Data cells
                    metric = analysis.index[row - 1] if row > 0 else None
                    value = analysis.iloc[row - 1, col - 1] if row > 0 and col > 0 else None

                    # Ensure `value` is a valid string before calling `.strip()`**
                    if isinstance(value, str):
                        value = value.strip()

                        # Skip styling if the cell is empty or contains only `+`, `-`, `=`**
                        if value == "" or trend_symbol_pattern.fullmatch(value):
                            continue  # Leave these cells white (default)

                        # Convert string-based numbers to numeric values safely
                        value = pd.to_numeric(value.replace('+', '').replace('-', '').replace('/', '').replace('=', ''), errors='coerce')

                    # *Skip `None` values completely (leave them white)**
                    if value is None or pd.isna(value):
                        continue

                    # Default cell color
                    color = "white"

                    # Apply color coding for specific metrics
                    if metric == 'Avg SBP (mmHg)':
                        color = 'lightgreen' if value < 130 else 'yellow' if value <= 139 else 'lightcoral'
                    elif metric == 'Avg DBP (mmHg)':
                        color = 'lightgreen' if value < 80 else 'yellow' if value <= 89 else 'lightcoral'
                    elif metric == 'SBP SD (mmHg)':
                        color = 'lightgreen' if value < 7.5 else 'yellow' if value < 15 else 'lightcoral'
                    elif metric == 'DBP SD (mmHg)':
                        color = 'lightgreen' if value < 5 else 'yellow' if value < 11.5 else 'lightcoral'
                    elif metric == 'SBP CV (%)':
                        color = 'lightgreen' if value < 5.5 else 'yellow' if value < 11 else 'lightcoral'
                    elif metric == 'DBP CV (%)':
                        color = 'lightgreen' if value < 6 else 'yellow' if value < 13 else 'lightcoral'
                    elif metric == 'Peak SBP² (mmHg)':
                        color = 'lightgreen' if value < 170 else 'lightcoral'
                    elif metric == 'Peak DBP² (mmHg)':
                        color = 'lightgreen' if value < 110 else 'lightcoral'

                    cell.set_facecolor(color)

            ax.set_title(report_title)

            # Dynamically position footnotes below the table
            table_bbox = table.get_window_extent(ax.figure.canvas.get_renderer()).transformed(ax.transAxes.inverted())
            table_bottom = table_bbox.y0  # Get table's bottom y-coordinate
            footnote_y_offset = 0.03  # Space between table and footnotes

            # ¹ ² ³ ⁴ ⁵ ⁶ ⁷ ⁸ ⁹
            footnotes = [
                '¹ "+" or "-" indicates the progress point allocation. "=" or blank cells indicate no points were allocated for the respective metric.',
                "² 'Peak' values represent the average of the three highest values in the timeframe.",
                "³ 'Low' values represent the single lowest value in the timeframe.",
                "⁴ 'Hypotensive Count' indicates the number of systolic BP values <= 95 mmHg with a hypothetical average decrease of 5 mmHg."
            ]

            # Add footnotes below the table
            for i, text in enumerate(footnotes):
                ax.text(0, table_bottom - (i + 1) * footnote_y_offset, text,
                        fontsize=8, transform=ax.transAxes, ha='left', va='top')

            pdf.savefig(fig)
            plt.close(fig)

            # Handle extremes table
            if extremes.empty:
                fig, ax = plt.subplots(figsize=(10, 6))
                ax.axis('off')
                ax.axis('tight')
                ax.text(0.5, 0.5, 'No extreme values found', transform=ax.transAxes, ha='center', va='center')
                ax.set_title(f"{report_title} - Extremes")
                pdf.savefig(fig)
                plt.close(fig)
            else:
                rows_per_page = 25
                total_rows = len(extremes)
                num_pages = (total_rows // rows_per_page) + (1 if total_rows % rows_per_page != 0 else 0)

                for page in range(num_pages):
                    start_row = page * rows_per_page
                    end_row = min(start_row + rows_per_page, total_rows)
                    fig, ax = plt.subplots(figsize=(10, 6))
                    ax.axis('off')
                    ax.axis('tight')

                    subset = extremes.iloc[start_row:end_row]
                    ax.table(cellText=subset.values,
                            colLabels=['Date', 'Systolic BP', 'Diastolic BP'],
                            cellLoc='center', loc='center')

                    ax.set_title(f"{report_title} - Extremes (Page {page + 1} of {num_pages})")
                    pdf.savefig(fig)
                    plt.close(fig)

        pdf_buffer.seek(0)  # Reset buffer position to the beginning
        return pdf_buffer


    def get_time_distribution_graph(self) -> str:
        if self.bpm_df is None or self.bpm_df.empty:
            raise ValueError("bpm_df is not set or is empty.")

        df = self.bpm_df.copy()
        df['timestamp_local'] = pd.to_datetime(df['timestamp_local'])
        df['hour'] = df['timestamp_local'].dt.hour

        # Melt for box plot
        df_melted = df.melt(
            id_vars='hour',
            value_vars=['systolic', 'diastolic'],
            var_name='Measurement',
            value_name='Value'
        )

        # Count of total measurements per hour
        counts = df.groupby('hour').size().reset_index(name='count')

        # Create subplot layout
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.1,
            row_heights=[0.7, 0.3],
            subplot_titles=("Blood Pressure Distribution by Hour", "Number of Measurements per Hour")
        )

        # Box plots (top)
        for measurement in ['systolic', 'diastolic']:
            filtered = df_melted[df_melted['Measurement'] == measurement]
            fig.add_trace(
                go.Box(
                    x=filtered['hour'],
                    y=filtered['Value'],
                    name=measurement.capitalize(),
                    boxmean=True
                ),
                row=1, col=1
            )

        # Bar chart (bottom)
        fig.add_trace(
            go.Bar(
                x=counts['hour'],
                y=counts['count'],
                marker_color='lightgray',
                name='Measurement Count'
            ),
            row=2, col=1
        )

        # Layout tweaks
        fig.update_layout(
            height=600,
            margin=dict(l=40, r=40, t=30, b=40),
            showlegend=True,
            autosize=True
        )
        fig.update_xaxes(title_text="Hour of Day", tickmode='linear', dtick=1, row=2, col=1)
        fig.update_yaxes(title_text="BP (mmHg)", row=1, col=1)
        fig.update_yaxes(title_text="Count", row=2, col=1)

        return pio.to_html(
            fig,
            full_html=False,
            include_plotlyjs=False,
            config={'responsive': True}
        )

    def generate_custom_report ( self, columns, extremes_filter_cols=None, report_title="Custom Report" ) :
        """
        Generates a downloadable PDF report (using save_to_pdf) that includes only the columns (from the analysis dataframe) provided by the user.
        Optionally, if extremes_filter_cols is provided, the extremes df is filtered (using extremes[ extremes_filter_cols ]) before being passed to save_to_pdf.
        :param columns: (list) – A list of column names (from analysis_df) to include in the report.
        :param extremes_filter_cols: (list, optional) – A list of column names (from extremes df) to filter extremes. If None, the entire extremes df is used.
        :param report_title: (str, optional) – A title for the report (default is "Custom Report").
        :return: (io.BytesIO) – A BytesIO buffer containing the generated PDF.
        """
        if not self.analysis_df is not None :
             raise ValueError (" analysis_df is not set (or is None). Call initialize_data (or calculate_analysis) first." )
        if not columns :
             raise ValueError (" columns must be a non-empty list." )
        # Filter analysis_df to include only the columns provided (and the index, so that the metric names are present)
        filtered_analysis = self.analysis_df[ columns ].copy ( )
        # (Optional) filter extremes df if extremes_filter_cols is provided
        extremes_df = self.calculate_extremes ( )
        if extremes_filter_cols is not None :
             extremes_df = extremes_df[ extremes_filter_cols ]
        # Call save_to_pdf (using the filtered dfs) and return the BytesIO buffer
        return self.save_to_pdf ( filtered_analysis, extremes_df, report_title )
