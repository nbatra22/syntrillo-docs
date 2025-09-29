import pandas as pd
import uuid
from datetime import datetime

def get_start_date(syntrillo_internal_key: uuid.UUID) -> datetime:
    """
    Start date is the date of the initial telemedicine visit.
    """
    return syntrillo_internal_key.timestamp_local

def get_time_intervals(start_date: datetime, bp_df: pd.DataFrame) -> dict:
    """
    Get the time intervals for the blood pressure data.

    Args:
        start_date: date of the telemedicine visit
        bp_df: blood pressure dataframe

    Returns:
        A dictionary with the time intervals.
        The keys are the time intervals and the values are the blood pressure data.
        The time intervals are:
            - "Baseline" (first 20 measurements)
            - "1mo" (Last 10 measurements leading up to cutoff)
            - "2mo" (Last 10 measurements leading up to cutoff)
            - "3mo" (Last 10 measurements leading up to cutoff)
            - "4mo" (Last 10 measurements leading up to cutoff)
            - "5mo" (Last 10 measurements leading up to cutoff)
            - "6mo" (Last 10 measurements leading up to cutoff)
            - "Latest" (Last 10 measurements)
    """
    return bp_df['timestamp_local'].min(), bp_df['timestamp_local'].max()
