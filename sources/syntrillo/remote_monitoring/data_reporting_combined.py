import uuid
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone
from typing import Tuple

from syntrillo.remote_monitoring.syntrillo_database_manager import SyntrilloDatabaseManager
from syntrillo.pseudonyms_management.lookup_codes_management import LookUpCodesManagement
from syntrillo.remote_monitoring.data_reporting_medication_adherence import DataReportingMedicationAdherence
from syntrillo.remote_monitoring.data_reporting_blood_pressure import DataReportingBloodPressure
from syntrillo.remote_monitoring.data_reporting_heart_rate import DataReportingHeartRate


from syntrillo.helper_functions.time import get_date_ranges_for_reporting


class DataReportingCombination:
    """
    Combine data from different Tenovi sources for a user.

    The objective is to produce dataframes used to display cardiovascular data in the Syntrillo CarePlan or CDSS dashboards.

    For given date ranges, dataframes include summary statistics, color coding, and other information to help the user understand their health status.

    This class call the other data reporting classes of thie remote_monitoring module to get the data and combine it.

    Typically this class is instantited once and all data is gatheres. Then the date ranges are selected and the data is filtered. This prevents multiple calls to the database.

    Args:
        syntrillo_internal_key: The internal key of the user in the Syntrillo database.


    """

    # class variables
    syntrillo_internal_key : uuid.UUID = None
    syntrillo_database_manager : SyntrilloDatabaseManager = None

    data_reporting_blood_pressure : DataReportingBloodPressure = None
    data_reporting_heart_rate : DataReportingHeartRate = None

    blood_pressure : bool = False
    heart_rate : bool = False

    blood_pressure_df : pd.DataFrame = None
    pulse_df : pd.DataFrame = None
    irregular_heartbeat_df : pd.DataFrame = None

    min_timestamp : datetime = None
    max_timestamp : datetime = None

    date_ranges : pd.DataFrame = None

    combined_summary : pd.DataFrame = None

    alpha : float = 0.5

    def __init__(self, syntrillo_internal_key : uuid.UUID) -> None:
        self.syntrillo_internal_key = syntrillo_internal_key

        # set up PHI database connection for this user
        self.syntrillo_database_manager = SyntrilloDatabaseManager(syntrillo_internal_key)

    def select_sources_and_obtain_data(
        self,
        blood_pressure: bool = True,
        heart_rate: bool = True,
    ) -> None:
        """
        Select the sources of data to include in the report, and obtain the data. All available data is obtained once to limit database calls. Data is stored in each class instance. Stats can be performed on specific date ranges in these instances.

        Args:
            blood_pressure: Include blood pressure data.
            heart_rate: Include heart_rate data.
        """
        self.blood_pressure = blood_pressure
        self.heart_rate = heart_rate

        # obtain data
        if blood_pressure:
            self.data_reporting_blood_pressure = DataReportingBloodPressure(self.syntrillo_internal_key)
            self.blood_pressure_df, _ = self.data_reporting_blood_pressure.get_blood_pressure_dataframe()

        if heart_rate:
            self.data_reporting_heart_rate = DataReportingHeartRate(self.syntrillo_internal_key)
            self.pulse_df, _ = self.data_reporting_heart_rate.get_pulse_dataframe()
            self.irregular_heartbeat_df, _ = self.data_reporting_heart_rate.get_irregular_heartbeat_dataframe()
            self.heart_rate_statistics_df, _ = self.data_reporting_heart_rate.get_heart_rate_statistics_dataframe()

        # get min and max timestamps from all dataframes
        min_timestamp = None
        max_timestamp = None
        if blood_pressure:
            min_timestamp = self.blood_pressure_df['timestamp_local'].min()
            max_timestamp = self.blood_pressure_df['timestamp_local'].max()
        if heart_rate:
            if min_timestamp is None:
                min_timestamp = self.pulse_df['timestamp_local'].min()
                max_timestamp = self.pulse_df['timestamp_local'].max()
            else:
                min_timestamp = min(min_timestamp, self.pulse_df['timestamp_local'].min())
                max_timestamp = max(max_timestamp, self.pulse_df['timestamp_local'].max())
            if min_timestamp is None:
                min_timestamp = self.irregular_heartbeat_df['timestamp_local'].min()
                max_timestamp = self.irregular_heartbeat_df['timestamp_local'].max()
            else:
                min_timestamp = min(min_timestamp, self.irregular_heartbeat_df['timestamp_local'].min())
                max_timestamp = max(max_timestamp, self.irregular_heartbeat_df['timestamp_local'].max())

        # if mix or max timestampe dont have a datetime type, assume they are str with datetime isoformat and convert
        if not isinstance(min_timestamp, datetime):
            min_timestamp = datetime.fromisoformat(min_timestamp)
        if not isinstance(max_timestamp, datetime):
            max_timestamp = datetime.fromisoformat(max_timestamp)

        self.min_timestamp = min_timestamp
        self.max_timestamp = max_timestamp

    def select_date_ranges(
        self,
        start_date: datetime = None,
        end_date: datetime = None,
        period: str = 'weekly', # or monthly
        last_ranges_unit : str = None, # 'week', or 'month', or 'day'
        use_total: bool = False, # whether to use total days or weeks for range name
        add_whole_range: bool = True, # whether to add a range for the whole period at the begining of the dataframe
        whole_period_name: str = 'Whole Period', # name for the whole period range
    ) -> dict :
        """
        - Give date ranges. If none: all will be selected from all sources, and min/max dates will be used.
        - Give expected layout of final dataframe : period, last_units

        delivers a dataframe with the date ranges for the period requested

        Args:
        - from_date: datetime object, beginning of the period
        - to_date: datetime object, end of the period
        - period: str, 'weekly' or 'monthly' : the period for the ranges
        - last_ranges_unit: str, 'month' or 'week' or 'day' : defines how to handle the last ranges. None will default to 'week' for weekly and 'month' for monthly
                For example:
                - if period is weekly and last_ranges_unit is 'week', the last range will be a single row with the remaining days (less than 7)  (default)
                - if period is weekly and last_ranges_unit is 'day', the last ranges will be several days ranges with 1 day each
                - if period is monthly and last_ranges_unit is 'month', the last range will be a single row with the remaining days (less than 30) (default)
                - if period is monthly and last_ranges_unit is 'week', the last ranges will be several weeks ranges with 7 days each
                - if period is monthly and last_ranges_unit is 'day', the last ranges will be several days ranges with 1 day each
            - use_total: bool, whether to use total days or weeks for range name

        Returns:
            - log: dict with the following keys: success, message

        """

        # if no date ranges are given, use the min and max timestamps from the data
        if start_date is None:
            start_date = self.min_timestamp
        if end_date is None:
            end_date = self.max_timestamp

        # if no data, return en error
        if start_date is None or end_date is None:
            log = {
                'success': False,
                'message': 'No data available',
            }
            return log

        # get the date ranges
        self.date_ranges, log = get_date_ranges_for_reporting(
            from_date=start_date,
            to_date=end_date,
            period=period,
            last_ranges_unit=last_ranges_unit,
            use_total=use_total,
            add_whole_range=add_whole_range,
            whole_period_name=whole_period_name,
        )

        return log

    def get_summary_statistics(self) -> Tuple[pd.DataFrame, dict]:
        """
        Get summary statistics for the data in the date ranges and sources selected.

        Returns:
            - combined_summary: pd.DataFrame, a dataframe with the summary statistics for the data in the date ranges and sources selected
            - log: dict with the following keys: success, message

        """

        # check if date_ranges is not None and not empty
        if self.date_ranges is None or self.date_ranges.empty:
            log = {
                'success': False,
                'message': 'No date ranges selected',
            }
            return pd.DataFrame(), log

        # combined summary is initially a copy of date_ranges
        combined_summary = self.date_ranges.copy()

        # get summary for each source, if available, and append its columns to combined_summary using the date_ranges as index
        if self.blood_pressure:
            self.data_reporting_blood_pressure.alpha = self.alpha
            blood_pressure_summary_df, log1 = self.data_reporting_blood_pressure.get_summary_for_date_ranges(self.date_ranges)

            if log1['success']:
                combined_summary = pd.concat(
                    [
                     combined_summary.set_index(['from_date', 'to_date', 'range_name']),
                     blood_pressure_summary_df.set_index(['from_date', 'to_date', 'range_name']),
                     ],
                    axis=1,
                    join='inner',
                   ).reset_index() # returns from_date and to_date back to columns. This is necessary to avoid problems with the index when concatenating the next source summary
            else:
                return pd.DataFrame(), log1

        if self.heart_rate:
            pulse_summary_df, log2 = self.data_reporting_heart_rate.get_pulse_summary_for_date_ranges(self.date_ranges)

            if log2['success']:
                combined_summary = pd.concat(
                    [
                     combined_summary.set_index(['from_date', 'to_date', 'range_name']),
                     pulse_summary_df.set_index(['from_date', 'to_date', 'range_name']),
                     ],
                    axis=1,
                    join='inner',
                   ).reset_index()
            else:
                return pd.DataFrame(), log2

        # add range_name_info column, including the from_date and to_date
        combined_summary['range_name_info'] = \
            combined_summary['from_date'].dt.strftime('%b %d') + \
            ' to ' + \
            combined_summary['to_date'].dt.strftime('%b %d')

        log = {
            'success': True,
            'message': 'Summary statistics obtained',
        }

        self.combined_summary = combined_summary

        return combined_summary, log



if __name__ == '__main__':
# Example usage
    lookup_codes = LookUpCodesManagement()
    entry = lookup_codes.retrieve_entry_by_healthie_user_id('1035117') # 1051529 : Omar's "Patient One" / 1035117 : "Patient One"
    lookup_codes.close_connection()

    # ---
    # get data
    drc =  DataReportingCombination(entry['syntrillo_internal_key'])

    drc.select_sources_and_obtain_data(blood_pressure=True, heart_rate=True)

    log = drc.select_date_ranges(
        start_date=None,
        end_date=None,
        period='monthly',
        last_ranges_unit='week',
        use_total=False,
        add_whole_range=True,
        whole_period_name='Whole Period',
    )
    print(log)
    print(drc.date_ranges.head(5))
    print(drc.blood_pressure_df.head(10))

    df, log = drc.get_summary_statistics()

    print(log)

    print(df)

    pass
