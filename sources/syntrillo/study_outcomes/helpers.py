import pandas as pd
import uuid
from datetime import datetime, timedelta

from syntrillo.api_healthie.forms import HealthieForms
from syntrillo.system.local_environment_and_secrets import LocalEnvironmentAndSecrets
from syntrillo.remote_monitoring.syntrillo_database_manager import SyntrilloDatabaseManager

def get_start_date(healthie_user_id: str) -> datetime:
    """
    Start date is the date of the initial telemedicine visit.
    """
    form_id, module_id = SyntrilloDatabaseManager().get_form_and_module_ids_by_module_label('telemed_date_of_service')

    forms_manager = HealthieForms()
    response = forms_manager.get_first_telemed_form(healthie_user_id, form_id)

    if response is None or len(response['formAnswerGroups']) == 0:
        return None

    first_form = response['formAnswerGroups'][0]
    form_answers = first_form['form_answers']

    for answer in form_answers:
        if answer['custom_module']['id'] == module_id:
            timestamp = answer['displayed_answer']
            return timestamp

    timestamp = first_form['created_at']
    return timestamp

def get_bp_time_intervals(start_date: datetime, bp_df: pd.DataFrame) -> dict:
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

    # Helper function to get last N measurements before a cutoff date
    def get_last_n_before_cutoff(df, cutoff_date, n=10):
        filtered = df[df['timestamp_local'] <= cutoff_date]
        last_n = filtered.tail(n)
        if len(last_n) > 0:
            return last_n, last_n['timestamp_local'].min(), cutoff_date
        return pd.DataFrame(), None, cutoff_date

    # Baseline: first 20 measurements
    baseline_data = bp_df.head(20)
    baseline_end = baseline_data['timestamp_local'].max() if len(baseline_data) > 0 else start_date

    data = {
        "Baseline": {
            "start_date": start_date,
            "end_date": baseline_end,
            "data": baseline_data,
        },
    }

    # Monthly intervals: last 10 measurements leading up to each monthly cutoff
    for month_num in range(1, 7):
        cutoff_date = start_date + timedelta(days=30 * month_num)
        month_data, month_start, month_end = get_last_n_before_cutoff(bp_df, cutoff_date, n=10)
        data[f"{month_num}mo"] = {
            "start_date": month_start if month_start else cutoff_date,
            "end_date": month_end,
            "data": month_data,
        }

    # Latest: last 10 measurements overall
    latest_data = bp_df.tail(10)
    latest_start = latest_data['timestamp_local'].min() if len(latest_data) > 0 else bp_df['timestamp_local'].max()
    latest_end = bp_df['timestamp_local'].max() if len(bp_df) > 0 else start_date

    data["Latest"] = {
        "start_date": latest_start,
        "end_date": latest_end,
        "data": latest_data,
    }

    return data

def calculate_engagement(time_interval_data: dict, bpm_df: pd.DataFrame) -> dict:
    """
    Calculate the engagement from the time interval data.
    """
    return time_interval_data

if __name__ == "__main__":
    healthie_user_id = "1525423"
    start_date = get_start_date(healthie_user_id)
    print(start_date)
