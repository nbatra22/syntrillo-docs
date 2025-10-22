import uuid
import pandas as pd
from datetime import datetime, timedelta
from typing import Tuple
from dateutil import parser
from syntrillo.bp_analysis.bp_analysis import BloodPressureAnalysis
from syntrillo.remote_monitoring.syntrillo_database_manager import SyntrilloDatabaseManager
from syntrillo.pseudonyms_management.lookup_codes_management import LookUpCodesManagement
from syntrillo.api_healthie.forms import HealthieForms
from syntrillo.api_healthie.metrics import HealthieMetrics

class PatientStudyOutcomes:
    """
    Retrieves the study outcomes for a patient.
    """

    syntrillo_internal_key: uuid.UUID = None
    healthie_user_id: str = None
    bp_df: pd.DataFrame = None
    study_start_date: datetime = None
    study_end_date: datetime = None

    def __init__(self, syntrillo_internal_key, healthie_user_id):
        self.syntrillo_internal_key = syntrillo_internal_key
        self.healthie_user_id = healthie_user_id

    def get_study_outcomes(self):
        """
        Get the study outcomes for a patient.
        """
        start_date_str = self.get_start_date()
        today_date_str = datetime.now().isoformat()

        # Run only if patient has had a telemedicine visit
        if start_date_str is None:
            return None

        # Parse the start and today date strings to datetime objects
        start_date = parser.isoparse(start_date_str)
        today_date = parser.isoparse(today_date_str)
        self.study_start_date = start_date.isoformat()
        self.study_end_date = (start_date + timedelta(days=30 * 6)).isoformat()

        bp_analysis_manager = BloodPressureAnalysis(self.syntrillo_internal_key)
        bp_df, _ = bp_analysis_manager.get_blood_pressure_dataframe(start_date=start_date, end_date=today_date)

        if bp_df is None or bp_df.empty:
            return None

        bp_df = bp_df.sort_values(by='timestamp_local')
        self.bp_df = bp_df

        # Get the time intervals
        time_interval_data = self.get_bp_time_intervals(start_date=start_date, bp_df=bp_df)

        for time_interval, data in time_interval_data.items():
            # Get BP metadata
            time_interval_data[time_interval]['bp_metadata'] = bp_analysis_manager.calculate_timeframe_metadata(data['data']) if data['data'] is not None else None
            time_interval_data[time_interval]['bp_data'] = data['data'].to_dict(orient='records') if data['data'] is not None else None
            del time_interval_data[time_interval]['data'] # Remove the DataFrame from the time interval data

            # Get heart rate data
            hr_data, hr_metadata = self.get_heart_rate_data(data['start_date'], data['end_date'])
            time_interval_data[time_interval]['hr_data'] = hr_data
            time_interval_data[time_interval]['hr_metadata'] = hr_metadata

            # Get hs-CRP data
            if time_interval in ['Baseline', 'Current']:
                hs_crp_data = self.get_hs_crp_data(start_date=start_date, end_date=today_date)

                if time_interval == 'Baseline' and hs_crp_data is not None and len(hs_crp_data) > 0:
                    time_interval_data[time_interval]['hs_crp_data'] = hs_crp_data[0]
                elif time_interval == 'Current' and hs_crp_data is not None and len(hs_crp_data) > 1:
                    time_interval_data[time_interval]['hs_crp_data'] = hs_crp_data[-1]
                else:
                    time_interval_data[time_interval]['hs_crp_data'] = None
            else:
                hs_crp_data = self.get_hs_crp_data(start_date=data['start_date'], end_date=data['end_date'])
                time_interval_data[time_interval]['hs_crp_data'] = hs_crp_data[0] if hs_crp_data is not None and len(hs_crp_data) > 0 else None

            # Get engagement percentage
            time_interval_data[time_interval]['engagement'] = round(self.calculate_engagement(data['start_date'], data['end_date']), 1)

        print(f"-------- time_interval_data: {time_interval_data}")

        time_interval_data['Current'] = self.calculate_metric_status_and_progress(current_dict=time_interval_data['Current'], baseline_dict=time_interval_data['Baseline'])

        print(f"-------- time_interval_data: {time_interval_data}")

        return time_interval_data

    def get_start_date(self) -> datetime:
        """
        Retrieves the date of the initial telemedicine visit.

        Priority order:
            - Date of service module answer
            - 'created_at' field from the first telemedicine form

        If no telemedicine form is found, return None.
        """
        db_manager = SyntrilloDatabaseManager(self.syntrillo_internal_key)
        form_id, module_id = db_manager.get_form_module_ids_by_module_label('telemed_date_of_service')

        forms_manager = HealthieForms()
        response = forms_manager.get_first_telemed_form(self.healthie_user_id, form_id)

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

    def get_bp_time_intervals(self, start_date: datetime, bp_df: pd.DataFrame) -> dict:
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
        def get_last_n_before_cutoff(df, prior_date, cutoff_date, n=10):
            filtered = df[(df['timestamp_local'] >= prior_date) & (df['timestamp_local'] <= cutoff_date)]
            if len(filtered) > 0:
                return filtered.tail(n) if len(filtered) > n else filtered
            else:
                return None

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
            prior_date = cutoff_date - timedelta(days=29)
            month_data = get_last_n_before_cutoff(bp_df, prior_date, cutoff_date, n=10)
            data[f"{month_num}mo"] = {
                "start_date": prior_date,
                "end_date": cutoff_date,
                "data": month_data,
            }

        # Latest: last 10 measurements overall
        latest_data = bp_df.tail(10)
        latest_start = latest_data['timestamp_local'].min() if len(latest_data) > 0 else bp_df['timestamp_local'].max()
        latest_end = bp_df['timestamp_local'].max() if len(bp_df) > 0 else start_date

        data["Current"] = {
            "start_date": latest_start,
            "end_date": latest_end,
            "data": latest_data,
        }

        return data

    def get_heart_rate_data(self, start_date: datetime, end_date: datetime) -> Tuple[list, dict]:
        """
        Uses larger data between pulse and rhr and calculates average RHR and standard deviation of RHR.
        Returns a tuple with the heart rate data and the metadata.
        """
        pulse_data = self.get_pulse_data(start_date=start_date, end_date=end_date)
        rhr_data = self.get_rhr_data(start_date=start_date, end_date=end_date)

        if (pulse_data is None or len(pulse_data) == 0) and (rhr_data is None or len(rhr_data) == 0):
            return None, None

        if rhr_data is None:
            return pulse_data, self.calculate_heart_rate_metadata(pulse_data)

        if pulse_data is None:
            return rhr_data, self.calculate_heart_rate_metadata(rhr_data)

        if (len(pulse_data) > len(rhr_data)):
            return pulse_data, self.calculate_heart_rate_metadata(pulse_data)
        else:
            return rhr_data, self.calculate_heart_rate_metadata(rhr_data)


    def calculate_heart_rate_metadata(self, data: list) -> dict:
        """
        Calculate the RHR metadata.
        """
        data = pd.DataFrame(data)
        return {
            "average_rhr": round(data['metric_stat'].mean(), 1),
            "standard_deviation_rhr": round(data['metric_stat'].std(), 1),
        }

    def get_pulse_data(self, start_date: datetime, end_date: datetime) -> dict:
        """
        Get the pulse data.
        """
        healthie_metrics = HealthieMetrics()

        entries, log = healthie_metrics.get_metric_data(
            user_id=self.healthie_user_id,
            category=HealthieMetrics.HEALTHIE_METRICS_PULSE_CATEGORY,
            start_date=start_date,
            end_date=end_date,
        )

        if entries is None or len(entries) == 0 or log['success'] == False:
            return None

        return entries

    def get_rhr_data(self, start_date: datetime, end_date: datetime) -> dict:
        """
        Get the RHR data.
        """
        healthie_metrics = HealthieMetrics()
        entries, log = healthie_metrics.get_metric_data(
            user_id=self.healthie_user_id,
            category=HealthieMetrics.HEALTHIE_METRICS_RHR_CATEGORY,
            start_date=start_date,
            end_date=end_date,
        )
        if entries is None or len(entries) == 0 or log['success'] == False:
            return None

        return entries

    def get_hs_crp_data(self, start_date: datetime, end_date: datetime) -> dict:
        """
        Get the hs-CRP data.
        """
        healthie_metrics = HealthieMetrics()
        entries, log = healthie_metrics.get_metric_data(
            user_id=self.healthie_user_id,
            category=HealthieMetrics.HEALTHIE_METRICS_HS_CRP_CATEGORY,
            start_date=start_date,
            end_date=end_date,
        )
        if entries is None or len(entries) == 0 or log['success'] == False:
            return None

        return entries

    def calculate_engagement(self, start_date: datetime, end_date: datetime) -> float:
        """
        Calculate the engagement from the blood pressure data.

        Args:
            bp_df: blood pressure dataframe
            start_date: start date
            end_date: end date

        Returns:
            A float value representing the percentage of days a measurement was taken out of the total number of days in the period.
        """
        print(f"-------- start_date: {start_date}")
        print(f"-------- end_date: {end_date}")
        total_days = (end_date - start_date).days
        measurement_window = self.bp_df[(self.bp_df['timestamp_local'] >= start_date) & (self.bp_df['timestamp_local'] <= end_date)]
        days_with_measurements = measurement_window['timestamp_local'].dt.date.nunique()
        return (days_with_measurements / total_days) * 100

    def calculate_metric_status_and_progress(
        self,
        current_dict: dict, # current timeframe data dictionary
        baseline_dict: dict, # baseline timeframe data dictionary
    ) -> dict:
        """
        Calculate the status and progress of a metric.

        Args:
            current_dict: the current timeframe data dictionary
            baseline_dict: the baseline timeframe data dictionary

        Returns:
            Updated current_dict with the additional status and progress dict.
        """

        current_metrics = {
            'avg_sbp': current_dict['bp_metadata']['Avg SBP (mmHg)'],
            'sbp_sd': current_dict['bp_metadata']['SBP SD (mmHg)'],
            'avg_pp': current_dict['bp_metadata']['Avg PP (mmHg)'],
            'avg_dbp': current_dict['bp_metadata']['Avg DBP (mmHg)'],
            'hs_crp': current_dict['hs_crp_data']['metric_stat'] if current_dict['hs_crp_data'] is not None else None,
            'rhr': current_dict['hr_metadata']['average_rhr'],
            'hrv': current_dict['hr_metadata']['standard_deviation_rhr'],
            'engagement': current_dict['engagement'],
            'start_date': current_dict['start_date'],
            'end_date': current_dict['end_date'],
        }

        baseline_metrics = {
            'avg_sbp': baseline_dict['bp_metadata']['Avg SBP (mmHg)'],
            'sbp_sd': baseline_dict['bp_metadata']['SBP SD (mmHg)'],
            'avg_pp': baseline_dict['bp_metadata']['Avg PP (mmHg)'],
            'avg_dbp': baseline_dict['bp_metadata']['Avg DBP (mmHg)'],
            'hs_crp': baseline_dict['hs_crp_data']['metric_stat'] if baseline_dict['hs_crp_data'] is not None else None,
            'rhr': baseline_dict['hr_metadata']['average_rhr'],
            'hrv': baseline_dict['hr_metadata']['standard_deviation_rhr'],
            'engagement': baseline_dict['engagement'],
            'start_date': baseline_dict['start_date'],
            'end_date': baseline_dict['end_date'],
        }

        metric_goals = {
            'avg_sbp': baseline_metrics['avg_sbp'] - 10, # reduce by 10 mmHg
            'sbp_sd': baseline_metrics['sbp_sd'] - (baseline_metrics['sbp_sd'] * 0.1), # decrease by 10%
            'avg_pp': baseline_metrics['avg_pp'] - 5, # reduce by 5 mmHg
            'avg_dbp': baseline_metrics['avg_dbp'] - 5, # reduce by 5 mmHg
            'hs_crp': baseline_metrics['hs_crp'] > current_metrics['hs_crp'] if baseline_metrics['hs_crp'] is not None and current_metrics['hs_crp'] is not None else False, # reduce by 0 mg/L
            'rhr': baseline_metrics['rhr'] - 5, # reduce by 5 bpm
            'hrv': baseline_metrics['hrv'] + (baseline_metrics['hrv'] * 0.1), # increase by 10%
        }

        metric_targets = {
            'avg_sbp': -10,
            'sbp_sd': -0.1,
            'avg_pp': -5,
            'avg_dbp': -5,
            'hs_crp': True,
            'rhr': -5,
            'hrv': 0.1,
            'engagement': True,
        }

        if current_metrics['hs_crp'] is not None and baseline_metrics['hs_crp'] is not None and current_metrics['hs_crp'] > baseline_metrics['hs_crp']:
            hs_crp_progress = 100
        elif current_metrics['hs_crp'] is not None and baseline_metrics['hs_crp'] is not None and current_metrics['hs_crp'] < baseline_metrics['hs_crp']:
            hs_crp_progress = 0
        else:
            hs_crp_progress = None

        metric_progress = {
            'avg_sbp': round((current_metrics['avg_sbp'] - baseline_metrics['avg_sbp']) / metric_targets['avg_sbp'] * 100, 1),
            'sbp_sd': round(((current_metrics['sbp_sd'] - baseline_metrics['sbp_sd']) / baseline_metrics['sbp_sd']) / metric_goals['sbp_sd'] * 100, 1),
            'avg_pp': round((current_metrics['avg_pp'] - baseline_metrics['avg_pp']) / metric_targets['avg_pp'] * 100, 1),
            'avg_dbp': round((current_metrics['avg_dbp'] - baseline_metrics['avg_dbp']) / metric_targets['avg_dbp'] * 100, 1),
            'hs_crp': hs_crp_progress,
            'rhr': round((current_metrics['rhr'] - baseline_metrics['rhr']) / metric_targets['rhr'] * 100, 1),
            'hrv': round((baseline_metrics['hrv'] - current_metrics['hrv']) / (metric_targets['hrv'] - baseline_metrics['hrv']) * 100, 1),
            'engagement': round(current_metrics['engagement'], 1),
        }

        statuses = {
            0: 'Behind',
            1: 'On track',
            2: 'Completed',
            3: 'Unachieved'
        }

        # Parse study dates back to datetime objects if they're strings
        study_start_date = parser.isoparse(self.study_start_date) if isinstance(self.study_start_date, str) else self.study_start_date
        study_end_date = parser.isoparse(self.study_end_date) if isinstance(self.study_end_date, str) else self.study_end_date
        current_end_date = current_metrics['end_date']
        # Make today_date timezone-aware to match study dates
        today_date = datetime.now(study_start_date.tzinfo) if study_start_date.tzinfo else datetime.now()
        time_progress = (today_date - study_start_date).days
        time_progress_percentage = round((time_progress / (study_end_date - study_start_date).days) * 100, 1)

        progress_dict = {
            'study_progress': {
                'days_completed': time_progress,
                'days_remaining': (study_end_date - today_date).days,
                'percentage': time_progress_percentage,
            },
        }

        for metric, progress in metric_progress.items():
            if metric == 'engagement':
                progress_dict[metric] = {
                    'status': 'Completed' if current_metrics['engagement'] >= 90 else 'Behind',
                    'progress': None,
                }
                continue

            if metric == 'hs_crp' and hs_crp_progress is None:
                progress_dict[metric] = {
                    'status': 'N/A',
                    'progress': hs_crp_progress,
                }
                continue

            if time_progress_percentage >= 100:
                progress_dict[metric] = {
                    'status': 'Completed' if progress >= 100 else 'Unachieved',
                    'progress': progress,
                }
                continue

            if progress >= 100:
                progress_dict[metric] = {
                    'status': 'Completed',
                    'progress': progress,
                }
                continue
            elif progress > time_progress_percentage:
                progress_dict[metric] = {
                    'status': 'On track',
                    'progress': progress,
                }
                continue
            elif progress < time_progress_percentage:
                progress_dict[metric] = {
                    'status': 'Behind',
                    'progress': progress,
                }
                continue

        # print(f"-------- progress_dict: {progress_dict}")
        current_dict['progress'] = progress_dict

        return current_dict

if __name__ == "__main__":
    healthie_user_id = '1051529'

    lookup_codes = LookUpCodesManagement()
    entry = lookup_codes.retrieve_entry_by_healthie_user_id(healthie_user_id)
    syntrillo_internal_key = entry['syntrillo_internal_key']

    patient_study_outcomes = PatientStudyOutcomes(syntrillo_internal_key=syntrillo_internal_key, healthie_user_id=healthie_user_id)
    print(patient_study_outcomes.get_study_outcomes())
