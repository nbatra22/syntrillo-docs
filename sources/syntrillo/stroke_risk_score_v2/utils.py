import math
from datetime import datetime
from typing import Tuple
import uuid
import pandas as pd
from syntrillo.remote_monitoring.syntrillo_database_manager import SyntrilloDatabaseManager
from syntrillo.api_tenovi.device_measurements import DeviceMeasurements
from syntrillo.system.logger import logger

def calculate_bmi(weight, height):
    # BMI = Weight (lb) / Height (in)² x 703
    return weight / math.pow(height, 2) * 703


def get_tenovi_srs_data(syntrillo_internal_key: uuid.UUID, start_date: datetime, end_date: datetime) -> Tuple[pd.DataFrame, dict]:
    """
    Retrieves Tenovi data for a given timeframe and patient.
    """
    bp_data = get_tenovi_data_for_timeframe(syntrillo_internal_key, start_date, end_date)
    pass

def stratify_tenovi_data(df: pd.DataFrame, start_date: datetime, end_date: datetime) -> pd.DataFrame:
    """
    Stratifies Tenovi data into timeframes.
    """

    most_recent_date = df['timestamp_local'].max()
    current_start = most_recent_date - pd.Timedelta(weeks=2) + pd.Timedelta(days=1)

    baseline_start = df['timestamp_local'].min() # first date of data
    baseline_end = baseline_start + pd.Timedelta(weeks=2) # Baseline end is 2 weeks after baseline start
    baseline_df = df[(df['timestamp_local'] >= baseline_start) & (df['timestamp_local'] < baseline_end)]

    # Calculate total elapsed time in weeks
    total_weeks = (most_recent_date - baseline_start).days / 7

    # Define time ranges
    prior_end = current_start - pd.Timedelta(days=1)
    prior_start = prior_end - pd.Timedelta(weeks=1, days=6)

    # Minimum number of required measurements
    min_measurements = 3

    # Initialize timeframes in correct order
    timeframes = {}

    # Include Baseline first if at least 4 weeks of data and it has enough measurements
    if total_weeks >= 4 and is_valid_timeframe(baseline_df, min_measurements):
        # timeframes[f"Baseline ({baseline_start.strftime('%-m/%-d/%y')}-{baseline_end.strftime('%-m/%-d/%y')})"] = baseline_df
        timeframes[f"Baseline"] = (f"{baseline_start.strftime('%-m/%-d/%y')} - {baseline_end.strftime('%-m/%-d/%y')}", baseline_df)

    # Include Prior in the middle if at least 6 weeks of data and it has enough measurements
    prior_df = df[(df['timestamp_local'] >= prior_start) & (df['timestamp_local'] < prior_end)]
    if total_weeks >= 5 and is_valid_timeframe(prior_df, min_measurements):
        # timeframes[f"Prior ({prior_start.strftime('%-m/%-d/%y')}-{prior_end.strftime('%-m/%-d/%y')})"] = prior_df
        timeframes[f"Prior"] = (f"{prior_start.strftime('%-m/%-d/%y')} - {prior_end.strftime('%-m/%-d/%y')}", prior_df)

    # Always include Current last, but only if it has enough measurements
    current_df = df[df['timestamp_local'] >= current_start]
    if is_valid_timeframe(current_df, min_measurements):
        # Determine if latest_date is within 3 days of today
        today = datetime.now().date()
        if isinstance(most_recent_date, pd.Timestamp):
            most_recent_date_only = most_recent_date.date()
        else:
            most_recent_date_only = most_recent_date
        if (today - most_recent_date_only).days <= 3:
            last_timeframe_name = "Current"
        else:
            last_timeframe_name = "Latest"
        timeframes[f"{last_timeframe_name}"] = (f"{current_start.strftime('%-m/%-d/%y')} - {most_recent_date.strftime('%-m/%-d/%y')}", current_df)


    # print(f"---- Timeframed Data ----- {timeframes}")
    return timeframes

def get_tenovi_data_for_timeframe(syntrillo_internal_key: uuid.UUID, start_date: datetime, end_date: datetime) -> Tuple[pd.DataFrame, dict]:
    """
    Retrieves Tenovi data for a given timeframe and patient.

    Args:
        syntrillo_internal_key (uuid.UUID): The Syntrillo internal key
        start_date (datetime): The start date
        end_date (datetime): The end date

    Returns:
        df (pd.DataFrame): The Tenovi data
        log (dict): The log

    Raises:
        Exception: If no Tenovi data is found for the given timeframe
    """
    # Set up database manager
    db_manager = SyntrilloDatabaseManager(syntrillo_internal_key=syntrillo_internal_key)

    # Get Tenovi data for the given timeframe
    df, log = db_manager.get_tenovi_device_metric_data(
        metric_name=DeviceMeasurements.TENOVI_METRICS_BPM_BLOOD_PRESSURE,
        start_date=start_date,
        end_date=end_date
    )

    if (df is None) or df.empty or (log['success'] == False):
        logger.error(f"No Tenovi data found for the given timeframe: {start_date} to {end_date}")
        raise Exception(f"No Tenovi data found for the given timeframe: {start_date} to {end_date}")

    # rename columns: "value_1" = systolic, "value_2" = diastolic
    # Drop unnecessary columns: 'device_name', 'metric_name'
    df = df.rename(columns={'value_1': 'systolic', 'value_2': 'diastolic'})
    df = df.drop(columns=['device_name', 'metric_name'])

    # Make sure systolic and diastolic values are numeric
    df['systolic'] = pd.to_numeric(df['systolic'], errors='coerce')
    df['diastolic'] = pd.to_numeric(df['diastolic'], errors='coerce')

    return df, log


def is_valid_timeframe(timeframe_df: pd.DataFrame, min_measurements: int = 3) -> bool:
    """Check if a timeframe has at least one valid (non-null) measurement and meets the min count."""
    return len(timeframe_df.dropna()) >= min_measurements and timeframe_df.notna().any().any()