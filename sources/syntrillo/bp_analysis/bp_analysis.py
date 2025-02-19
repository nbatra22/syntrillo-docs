import uuid
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone
import plotly.graph_objs as go
import plotly.io as pio
import plotly.utils as pu
from typing import Tuple
import matplotlib
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.pyplot as plt
from PyPDF2 import PdfMerger
import textwrap
import io

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet

matplotlib.use('Agg')

from syntrillo.system.matplotlib_setup import setup_matplotlib
setup_matplotlib()

import matplotlib.cm as cm
import matplotlib.colors as mcolors
from matplotlib import colormaps

from syntrillo.remote_monitoring.syntrillo_database_manager import SyntrilloDatabaseManager
from syntrillo.api_tenovi.device_types import DeviceTypes
from syntrillo.api_tenovi.device_measurements import DeviceMeasurements
from syntrillo.pseudonyms_management.lookup_codes_management import LookUpCodesManagement

from syntrillo.clinical_decision_support.color_coding.blood_pressure_categories import ColorCodingBloodPressureCategories, ColorCodingBloodPressureCategoriesWrapper
from syntrillo.clinical_decision_support.color_coding.blood_pressure_rainbow import ColorCodingBloodPressureRainbows

from syntrillo.bp_analysis.functions.determine_cell_color import determine_cell_color

class BloodPressureAnalysis:
    """
    Handle patient level blood pressure analysis, including:
        - Avg SBP/DBP
        - SBP/DBP standard deviation (SD)
        - SBP/DBP coefficent of variation (CV)
        - Peak SBP/DBP (avg of top 3)
        - Low SBP/DBP
        - Hyper/hypotensive counts
        - Progress Point calculation (per Tech Roadmap slide deck)
    """

    # class variables
    syntrillo_internal_key : uuid.UUID = None
    syntrillo_database_manager : SyntrilloDatabaseManager = None
    bpm_df : pd.DataFrame = None
    """
        bpf_df = {
            "timestamp_local": timestamp
            "systolic": int
            "diastolic": int
        }
    """
    timeframed_data : dict = None
    HYPERTENSION_SBP_THRESHOLD = 170
    HYPERTENSION_DBP_THRESHOLD = 110
    HYPOTENSION_SBP_THRESHOLD = 95

    # color maps for systolic and diastolic
    alpha : float = 0.5

    # no data string
    no_data_string : str = "no data"


    def __init__(self, syntrillo_internal_key : uuid.UUID) -> None:

        self.syntrillo_internal_key = syntrillo_internal_key

        # set up PHI database connection for this user
        self.syntrillo_database_manager = SyntrilloDatabaseManager(syntrillo_internal_key)

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
                'error': 'No BPM blood_pressure data found',
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

    def calculate_metadata(self):
        df = self.bpm_df

        counts = {
            'Avg SBP (mmHg)': round(df['systolic'].mean(), 2),
            'Avg DBP (mmHg)': round(df['diastolic'].mean(), 2),
            'Peak SBP² (mmHg)': round(df['systolic'].nlargest(3).mean(), 2),
            'Peak DBP² (mmHg)': round(df['diastolic'].nlargest(3).mean(), 2),
            'Low SBP³ (mmHg)': round(df['systolic'].min(), 2),
            'Low DBP³ (mmHg)': round(df['diastolic'].min(), 2),
            'SBP SD (mmHg)': round(df['systolic'].std(), 2),
            'DBP SD (mmHg)': round(df['diastolic'].std(), 2),
            'SBP CV (%)': round((df['systolic'].std() / df['systolic'].mean()) * 100, 2) if df['systolic'].mean() != 0 else None,
            'DBP CV (%)': round((df['diastolic'].std() / df['diastolic'].mean()) * 100, 2) if df['diastolic'].mean() != 0 else None,
            # 'SBP Count (>= 160)': len(df[df['systolic'] >= 160]),
            # 'SBP Count (>= 165)': len(df[df['systolic'] >= 165]),
            'SBP Count (>= 170)': len(df[df['systolic'] >= 170]),
            'SBP Count (>= 175)': len(df[df['systolic'] >= 175]),
            # 'SBP Count (<=80)': len(df[df['systolic'] <= 80]),
            # 'SBP Count (<=85)': len(df[df['systolic'] <= 85]),
            # 'SBP Count (<=90)': len(df[df['systolic'] <= 90]),
            # 'SBP Count (<=95)': len(df[df['systolic'] <= 95]),
            'Hypotensive Count⁴': len(df[df['systolic'] <= 100]),
        }

        return counts


    def calculate_timeframes(self) -> dict:
        df = self.bpm_df

        latest_date = df['timestamp_local'].max()
        current_start = latest_date - pd.Timedelta(weeks=2) + pd.Timedelta(days=1)

        baseline_start = df['timestamp_local'].min()
        baseline_end = df['timestamp_local'].min() + pd.Timedelta(weeks=1, days=6)

        prior_end = current_start - pd.Timedelta(days=1)
        prior_start = prior_end - pd.Timedelta(weeks=1, days=6)

        timeframes = {
            f"Baseline ({baseline_start.strftime('%m/%d/%y')}-{baseline_end.strftime('%m/%d/%y')})": df[(df['timestamp_local'] >= baseline_start) & (df['timestamp_local'] < baseline_end)],
            f"Prior ({prior_start.strftime('%m/%d/%y')}-{prior_end.strftime('%m/%d/%y')})": df[(df['timestamp_local'] >= prior_start) & (df['timestamp_local'] < prior_end)],
            # f"Current ({prior_end.strftime('%m/%d/%y')}-{latest_date.strftime('%m/%d/%y')})": df[df['timestamp_local'] >= prior_end]
            f"Current¹ ({current_start.strftime('%m/%d/%y')}-{latest_date.strftime('%m/%d/%y')})": df[df['timestamp_local'] >= current_start]
        }

        self.timeframed_data = timeframes

        return timeframes


    def calculate_analysis(self) -> pd.DataFrame:
        timeframes = self.timeframed_data

        analysis = {}
        current_timeframe = next((name for name in timeframes if name.startswith("Current")), None)
        prior_timeframe = next((name for name in timeframes if name.startswith("Prior")), None)
        baseline_timeframe = next((name for name in timeframes if name.startswith("Baseline")), None)

        for name, frame in timeframes.items():
            if frame.empty:
                analysis[name] = {
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
                    # 'SBP Count (>= 160)': None,
                    # 'SBP Count (>= 165)': None,
                    'SBP Count (>= 170)': None,
                    'SBP Count (>= 175)': None,
                    # 'SBP Count (<=80)': None,
                    # 'SBP Count (<=85)': None,
                    # 'SBP Count (<=90)': None,
                    # 'SBP Count (<=95)': None,
                    'Hypotensive Count⁴': None,
                }
                continue

            avg_systolic = round(frame['systolic'].mean(), 2)
            avg_diastolic = round(frame['diastolic'].mean(), 2)
            peak_systolic = round(frame['systolic'].nlargest(3).mean(), 2)  # Avg of 3 highest values
            peak_diastolic = round(frame['diastolic'].nlargest(3).mean(), 2)  # Avg of 3 highest values
            low_systolic = round(frame['systolic'].min(), 2)
            low_diastolic = round(frame['diastolic'].min(), 2)
            systolic_sd = round(frame['systolic'].std(), 2)
            diastolic_sd = round(frame['diastolic'].std(), 2)
            systolic_cv = round((systolic_sd / avg_systolic) * 100, 2) if avg_systolic else None
            diastolic_cv = round((diastolic_sd / avg_diastolic) * 100, 2) if avg_diastolic else None
            sbp_count_160 = len(frame[frame['systolic'] >= 160])
            sbp_count_165 = len(frame[frame['systolic'] >= 165])
            sbp_count_170 = len(frame[frame['systolic'] >= 170])
            sbp_count_175 = len(frame[frame['systolic'] >= 175])
            sbp_count_80 = len(frame[frame['systolic'] <= 80])
            sbp_count_85 = len(frame[frame['systolic'] <= 85])
            sbp_count_90 = len(frame[frame['systolic'] <= 90])
            sbp_count_95 = len(frame[frame['systolic'] <= 95])
            hypertensive_dbp_count = len(frame[frame['diastolic'] >= self.HYPERTENSION_DBP_THRESHOLD])
            hypotensive_count = len(frame[frame['systolic'] <= self.HYPOTENSION_SBP_THRESHOLD + 5])


            analysis[name] = {
                'Avg SBP (mmHg)': avg_systolic,
                'Avg DBP (mmHg)': avg_diastolic,
                'Peak SBP² (mmHg)': peak_systolic,
                'Peak DBP² (mmHg)': peak_diastolic,
                'Low SBP³ (mmHg)': low_systolic,
                'Low DBP³ (mmHg)': low_diastolic,
                'SBP SD (mmHg)': systolic_sd,
                'DBP SD (mmHg)': diastolic_sd,
                'SBP CV (%)': systolic_cv,
                'DBP CV (%)': diastolic_cv,
                # 'SBP Count (>= 160)': sbp_count_160,
                # 'SBP Count (>= 165)': sbp_count_165,
                'SBP Count (>= 170)': sbp_count_170,
                'SBP Count (>= 175)': sbp_count_175,
                # 'SBP Count (<=80)': sbp_count_80,
                # 'SBP Count (<=85)': sbp_count_85,
                # 'SBP Count (<=90)': sbp_count_90,
                # 'SBP Count (<=95)': sbp_count_95,
                'Hypotensive Count⁴': hypotensive_count,
            }

        points = {
            'Avg SBP (mmHg)': {'increase': -2, 'decrease': 2},
            'Avg DBP (mmHg)': {'increase': -2, 'decrease': 2},
            'SBP CV (%)': {'increase': -1, 'decrease': 1},
            'DBP CV (%)': {'increase': -1, 'decrease': 1},
            'SBP SD (mmHg)': {'increase': -1, 'decrease': 1},
            'DBP SD (mmHg)': {'increase': -1, 'decrease': 1},
            'Peak SBP² (mmHg)': {'above_threshold': -2, 'below_threshold': 2},
            'Peak DBP² (mmHg)': {'above_threshold': -2, 'below_threshold': 2}
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

        delta = 0
        baseline_delta = 0

        if current_timeframe and prior_timeframe and baseline_timeframe:
            for metric in analysis[current_timeframe]:
                current_value = analysis[current_timeframe][metric]
                prior_value = analysis[prior_timeframe].get(metric, "-")
                baseline_value = analysis[baseline_timeframe].get(metric, "-")

                if current_value is not None and prior_value != "-" and baseline_value != "-" and isinstance(prior_value, (int, float)) and isinstance(baseline_value, (int, float)):
                    change = current_value - prior_value
                    percent_change = (
                        (current_value - prior_value) / prior_value * 100
                        if prior_value != 0
                        else 0
                    )
                    abs_change = abs(change)
                    abs_percent_change = abs(percent_change)

                    baseline_change = current_value - baseline_value
                    baseline_percent_change = (
                        (current_value - baseline_value) / baseline_value * 100
                        if baseline_value != 0
                        else 0
                    )
                    baseline_abs_change = abs(baseline_change)
                    baseline_abs_percent_change = abs(baseline_percent_change)


                    # Handle average SBP and DBP ------------------
                    if metric in ['Avg SBP (mmHg)', 'Avg DBP (mmHg)']:
                        if any(val > boundaries[metric][1] for val in [baseline_value, current_value, prior_value]):
                            curr_progress = "="  # Default for current change
                            base_progress = "="  # Default for baseline change

                            if change > 0:  # Increase in current change
                                delta += points[metric]['increase']
                                curr_progress = "-"  # Indicates a decrease is needed
                            elif change < 0:  # Decrease in current change
                                delta += points[metric]['decrease']
                                curr_progress = "+"  # Indicates an increase is needed

                            if baseline_change > 0:  # Increase in baseline change
                                baseline_delta += points[metric]['increase']
                                base_progress = "-"  # Indicates a decrease is needed
                            elif baseline_change < 0:  # Decrease in baseline change
                                baseline_delta += points[metric]['decrease']
                                base_progress = "+"  # Indicates an increase is needed

                            # Update progress format as "(current change sign) / (baseline change sign)"
                            progress = f"{curr_progress}/{base_progress}"

                            # Keep the last f-string with the updated progress
                            analysis[current_timeframe][metric] = f"{current_value} {progress}"

                    # Handle SBP-SD and DBP-SD ------------------
                    elif metric in ['SBP SD (mmHg)', 'DBP SD (mmHg)']:
                        if any(val > boundaries[metric][1] for val in [baseline_value, current_value, prior_value]):
                            curr_progress = "="  # Default for current change
                            base_progress = "="  # Default for baseline change
                            if abs_change >= thresholds[metric]:
                                if change > 0:  # Increase in current change
                                    delta += points[metric]['increase']
                                    curr_progress = "-"  # Indicates a decrease is needed
                                elif change < 0:  # Decrease in current change
                                    delta += points[metric]['decrease']
                                    curr_progress = "+"  # Indicates an increase is needed
                            if baseline_abs_change >= thresholds[metric]:
                                if baseline_change > 0:  # Increase in baseline change
                                    baseline_delta += points[metric]['increase']
                                    base_progress = "-"  # Indicates a decrease is needed
                                elif baseline_change < 0:  # Decrease in baseline change
                                    baseline_delta += points[metric]['decrease']
                                    base_progress = "+"  # Indicates an increase is needed

                            progress = f"{curr_progress}/{base_progress}"
                            analysis[current_timeframe][metric] = f"{current_value} {progress}"

                    # Handle SBP-CV and DBP-CV ------------------
                    elif metric in ['SBP CV (%)', 'DBP CV (%)']:
                        if any(val > boundaries[metric][1] for val in [baseline_value, current_value, prior_value]):
                            if abs_percent_change >= thresholds[metric]:
                                curr_progress = "="  # Default for current change
                                base_progress = "="  # Default for baseline change

                                if percent_change > 0:  # Increase in current change
                                    delta += points[metric]['increase']
                                    curr_progress = "-"  # Indicates a decrease is needed
                                elif percent_change < 0:  # Decrease in current change
                                    delta += points[metric]['decrease']
                                    curr_progress = "+"  # Indicates an increase is needed

                            if baseline_abs_percent_change >= thresholds[metric]:
                                if baseline_percent_change > 0:  # Increase in baseline change
                                    baseline_delta += points[metric]['increase']
                                    base_progress = "-"  # Indicates a decrease is needed
                                elif baseline_percent_change < 0:  # Decrease in baseline change
                                    baseline_delta += points[metric]['decrease']
                                    base_progress = "+"  # Indicates an increase is needed

                            progress = f"{curr_progress}/{base_progress}"
                            analysis[current_timeframe][metric] = f"{current_value} {progress}"

                    # Handle categorical change for Peak BP
                    elif metric.startswith('Peak') and isinstance(current_value, (int, float)):
                        if any(val > boundaries[metric][1] for val in [baseline_value, current_value, prior_value]):
                            high_threshold = thresholds[metric]
                            curr_progress = "="  # Default for current change
                            base_progress = "="  # Default for baseline change

                            # Current change logic
                            if prior_value < high_threshold < current_value:  # Crossed above threshold
                                delta += points[metric]['above_threshold']
                                curr_progress = "-"  # Indicates a decrease is needed
                            elif prior_value > high_threshold >= current_value:  # Crossed below threshold
                                delta += points[metric]['below_threshold']
                                curr_progress = "+"  # Indicates an increase is needed

                            # Baseline change logic
                            if baseline_value < high_threshold < current_value:  # Crossed above threshold
                                baseline_delta += points[metric]['above_threshold']
                                base_progress = "-"  # Indicates a decrease is needed
                            elif baseline_value > high_threshold >= current_value:  # Crossed below threshold
                                baseline_delta += points[metric]['below_threshold']
                                base_progress = "+"  # Indicates an increase is needed

                            progress = f"{curr_progress}/{base_progress}"
                            analysis[current_timeframe][metric] = f"{current_value} {progress}"


        # Add the total delta as a new key for the extra cell
        progress = "Improving" if delta > 0 else "Worsening" if delta < 0 else "Same"
        baseline_progress = "Improving" if baseline_delta > 0 else "Worsening" if baseline_delta < 0 else "Same"
        analysis[current_timeframe]['Progress (pts)'] = f"{progress} ({delta})"
        analysis[current_timeframe]['Baseline Progress (pts)'] = f"{baseline_progress} ({baseline_delta})"

        # Ensure the Progress row has "-" in baseline and prior columns
        analysis[prior_timeframe].setdefault('Progress (pts)', '-')
        analysis[next(k for k in analysis if "Baseline" in k)]['Progress (pts)'] = '-'
        analysis[prior_timeframe].setdefault('Baseline Progress (pts)', '-')
        analysis[next(k for k in analysis if "Baseline" in k)]['Baseline Progress (pts)'] = '-'

        df = pd.DataFrame.from_dict(analysis, orient='index').T

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

        df.loc['Overall'] = df.apply(calculate_overall, axis=0)

        return df


    def calculate_since_baseline(self, metadata, analysis_table):
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
        BLOOD_PRESSURE_LOW = 90
        BLOOD_PRESSURE_HIGH_VALUE1 = 170
        BLOOD_PRESSURE_HIGH_VALUE2 = 110
        df = self.bpm_df
        extremes = df[(df['systolic'] < BLOOD_PRESSURE_LOW) |
                  (df['systolic'] > BLOOD_PRESSURE_HIGH_VALUE1) |
                  (df['diastolic'] > BLOOD_PRESSURE_HIGH_VALUE2)]
        return extremes[['timestamp_local', 'systolic', 'diastolic']]

    # def generate_pdf(self, extremes):
    #     # Create an in-memory PDF buffer
    #     pdf_buffer = io.BytesIO()
    #     analysis = self.bpm_df

    #     def wrap_text(text, width=16):
    #         """Manually inserts line breaks to wrap text in table headers."""
    #         return "\n".join(textwrap.wrap(text, width))

    #     with PdfPages(pdf_buffer) as pdf:
    #         wrapped_col_labels = ['Metric'] + [wrap_text(col) for col in analysis.columns]

    #         # Analysis Table
    #         fig, ax = plt.subplots(figsize=(10, 6))
    #         ax.axis('off')
    #         ax.axis('tight')

    #         table = ax.table(cellText=analysis.reset_index().values,
    #                         colLabels=wrapped_col_labels,
    #                         cellLoc='center', loc='center')

    #         table.auto_set_font_size(False)
    #         table.scale(1.2, 1.2)

    #         # Adjust cell formatting
    #         for (row, col), cell in table.get_celld().items():
    #             if row == 0:  # Wrap text for column headers
    #                 cell.set_height(cell.get_height() * 2)
    #                 cell.set_fontsize(8)
    #                 cell.set_text_props(wrap=True)
    #             elif col == 0:  # Wrap text for row headers
    #                 cell.set_text_props(wrap=True)
    #                 cell.set_fontsize(8)
    #             else:  # Apply colorization logic
    #                 metric = analysis.index[row - 1] if row > 0 else None
    #                 value = analysis.iloc[row - 1, col - 1] if row > 0 and col > 0 else None
    #                 color = determine_cell_color(metric, value)
    #                 cell.set_facecolor(color)

    #         ax.set_title("Analysis Report")
    #         pdf.savefig(fig)
    #         plt.close(fig)

    #         # Extremes Table with Pagination
    #         rows_per_page = 25
    #         total_rows = len(extremes)
    #         num_pages = (total_rows // rows_per_page) + (1 if total_rows % rows_per_page != 0 else 0)

    #         if extremes.empty:
    #             fig, ax = plt.subplots(figsize=(10, 6))
    #             ax.axis('off')
    #             ax.axis('tight')
    #             ax.text(0.5, 0.5, 'No extreme values found', transform=ax.transAxes, ha='center', va='center')
    #             ax.set_title("Extremes Report")
    #             pdf.savefig(fig)
    #             plt.close(fig)
    #         else:
    #             for page in range(num_pages):
    #                 start_row = page * rows_per_page
    #                 end_row = min(start_row + rows_per_page, total_rows)
    #                 fig, ax = plt.subplots(figsize=(10, 6))
    #                 ax.axis('off')
    #                 ax.axis('tight')

    #                 subset = extremes.iloc[start_row:end_row]
    #                 ax.table(cellText=subset.values,
    #                         colLabels=['Date', 'Systolic BP', 'Diastolic BP'],
    #                         cellLoc='center', loc='center')
    #                 ax.set_title(f"Extremes Report (Page {page + 1} of {num_pages})")
    #                 pdf.savefig(fig)
    #                 plt.close(fig)

    #     # Ensure buffer is set to the beginning
    #     pdf_buffer.seek(0)

    #     return pdf_buffer

    def generate_pdf(self, analysis, extremes):
        """Generates a PDF with a formatted analysis table and extremes table using ReportLab."""

        pdf_buffer = io.BytesIO()
        doc = SimpleDocTemplate(pdf_buffer, pagesize=letter)
        elements = []
        styles = getSampleStyleSheet()

        def wrap_text(text, width=16):
            """Wraps text manually to fit table headers."""
            return "\n".join(textwrap.wrap(text, width))

        # **1️⃣ Analysis Table**
        wrapped_col_labels = ['Metric'] + [wrap_text(col) for col in analysis.columns]
        data = [wrapped_col_labels] + analysis.reset_index().values.tolist()

        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),  # Header background
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),  # Header text color
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),  # Center align
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),  # Bold header
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),  # Padding
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),  # Alternating row color
            ('GRID', (0, 0), (-1, -1), 1, colors.black)  # Grid lines
        ]))

        elements.append(Paragraph("Analysis Report", styles['Title']))
        elements.append(table)

        # **2️⃣ Extremes Table with Pagination**
        rows_per_page = 25
        total_rows = len(extremes)
        num_pages = (total_rows // rows_per_page) + (1 if total_rows % rows_per_page != 0 else 0)

        if extremes.empty:
            elements.append(Paragraph("No extreme values found", styles['Normal']))
        else:
            for page in range(num_pages):
                start_row = page * rows_per_page
                end_row = min(start_row + rows_per_page, total_rows)
                subset = extremes.iloc[start_row:end_row].values.tolist()

                extremes_table = Table([['Date', 'Systolic BP', 'Diastolic BP']] + subset)
                extremes_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))

                elements.append(Paragraph(f"Extremes Report (Page {page + 1} of {num_pages})", styles['Heading2']))
                elements.append(extremes_table)

        # **Build the PDF**
        doc.build(elements)
        pdf_buffer.seek(0)

        return pdf_buffer
