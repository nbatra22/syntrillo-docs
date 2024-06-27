import uuid
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone

from syntrillo.remote_monitoring.syntrillo_database_manager import SyntrilloDatabaseManager
from syntrillo.api_tenovi.device_types import DeviceTypes
from syntrillo.pseudonyms_management.lookup_codes_management import LookUpCodesManagement

class RemoteMonitoringDataReporting:

    def __init__(self, syntrillo_internal_key : uuid.UUID) -> None:
        """
        Get user level reports from the remote monitoring system

        Data from the remote monitoring system is stored in our PHI database

        Args:
            syntrillo_internal_key : uuid.UUID

        Returns:
            None

        """
        self.syntrillo_internal_key = syntrillo_internal_key

        # set up PHI database connection for this user
        self.syntrillo_database_manager = SyntrilloDatabaseManager(syntrillo_internal_key)


    def get_pillbox_report(
        self,
        start_date : datetime,
        end_date : datetime,
        expected_pattern : str = "twice daily",
        ):
        """
        Get pillbox report

        https://tenovi.com/hwi-device-overview/#tenovi-pillbox

        https://tenovi.com/tenovi-pillbox/

        https://tenovi.b-cdn.net/wp-content/uploads/2024/06/Pillbox_QSG_6.7.pdf

        Pillbox has 14 compartments. One AM and one PM compartment, for each day of the week.

        Available metrics:
          - pillbox_opened           : value_1 is day of the week (1=Sun, 7=Sat), value_2 is AM or PM (1=AM, 2=PM)
          - pillbox_refill_initiated : value_1=1
          - pillbox_refilled         : value_1 is day of the week (1=Sun, 7=Sat), value_2 is AM or PM (1=AM, 2=PM)

        Report:
         - number of missed doses
         - table of missed doses per day and AM/PM
         - number of refills initiated

        Args:
            start_date : datetime (if None: the date of the first pillbox event will be used)
            end_date : datetime (if None: the current date will be used)
            expected_pattern : str = "twice daily", "daily AM", "daily PM"

        Returns:

        """

        # deal with None start_date, end_date
        if start_date is None:
            start_date = datetime.now() - timedelta(days=30)
            # TODO : look for the first pillbox event and set start_date to that date
        if end_date is None:
            end_date = datetime.now()

        # get pillbox data from PHI database, ordered by timestamp
        pillbox_data, log = self.syntrillo_database_manager.get_tenovi_device_data(
            device_name=DeviceTypes.TENOVI_DEVICE_NAME__PILLBOX,
            start_date=start_date,
            end_date=end_date,
        )

        # get total number of pillbox_refilled events
        pillbox_refilled = pillbox_data[pillbox_data['metric_name'] == 'pillbox_refilled']
        pillbox_refilled_count = pillbox_refilled.shape[0]

        # get total number of pillbox_refill_initiated events
        pillbox_refill_initiated = pillbox_data[pillbox_data['metric_name'] == 'pillbox_refill_initiated']
        pillbox_refill_initiated_count = pillbox_refill_initiated.shape[0]

        # report if multiple pillbox_opened events for the same day and AM/PM. Give count of duplicates

        # get total number of pillbox_opened events, per day (value_1) and AM/PM (value_2)
        #   - create a new panda dataframe with 7 rows (one for each day of the week) and 2 columns (AM, PM). Initialize all values to 0.
        #   - row names are days of the week : sun=1, mon=2, ..., sat=7
        #   - each cell will store the number of pillbox_opened events for that day of the week and AM/PM
        #   - if multiple pillbox_opened events for the same day and AM/PM : count duplicates as one event
        pillbox_opened = pillbox_data[pillbox_data['metric_name'] == 'pillbox_opened']
        pillbox_opened_count = pillbox_opened.shape[0]
        pillbox_actual_opened_count_per_day_df = pd.DataFrame(np.zeros((7, 2)), columns=['AM', 'PM'])
        row_names = ['sun', 'mon', 'tue', 'wed', 'thu', 'fri', 'sat']
        pillbox_actual_opened_count_per_day_df.index = row_names
        current_row_date = None
        current_am_pm = None
        duplicate_count = 0
        for index, row in pillbox_opened.iterrows():
            # get date from row['timestamp_local'], which has this isoformat: '2024-06-26T15:43:08.000000-04:00'
            row_date = datetime.strptime(row['timestamp_local'], '%Y-%m-%dT%H:%M:%S.%f%z').date()
            day_of_week = int(round(float(row['value_1']), 0)) - 1
            am_pm = int(round(float(row['value_2']), 0)) - 1
            if row_date == current_row_date and am_pm == current_am_pm:
                duplicate_count += 1
                continue
            pillbox_actual_opened_count_per_day_df.iloc[day_of_week, am_pm] += 1
            current_row_date = row_date
            current_am_pm = am_pm

        print(pillbox_actual_opened_count_per_day_df)  # actual

        # build expected df from the expected pattern
        pillbox_expected_opened_count_per_day_df = pd.DataFrame(np.zeros((7, 2)), columns=['AM', 'PM'])
        row_names = ['sun', 'mon', 'tue', 'wed', 'thu', 'fri', 'sat']
        pillbox_expected_opened_count_per_day_df.index = row_names

        # loop for each day from start_date to end_date :
        # add 1 to the expected df for each day and AM/PM that matches the expected pattern
        current_day = start_date.date()
        while current_day <= end_date.date():
            # get day of the week
            day_of_week = current_day.weekday()
            # get expected AM/PM from expected pattern
            if expected_pattern == "twice daily":
                pillbox_expected_opened_count_per_day_df.iloc[day_of_week, 0] += 1
                pillbox_expected_opened_count_per_day_df.iloc[day_of_week, 1] += 1
            elif expected_pattern == "daily AM":
                pillbox_expected_opened_count_per_day_df.iloc[day_of_week, 0] += 1
            elif expected_pattern == "daily PM":
                pillbox_expected_opened_count_per_day_df.iloc[day_of_week, 1] += 1
            current_day += timedelta(days=1)

        print(pillbox_expected_opened_count_per_day_df)  # expected


        report = {
            'pillbox_refilled_count': pillbox_refilled_count,
            'pillbox_refill_initiated_count': pillbox_refill_initiated_count,
            'duplicate_count': duplicate_count,
        }

        return report, log


if __name__ == "__main__":
    # Example usage
    lookup_codes = LookUpCodesManagement()
    entry = lookup_codes.retrieve_entry_by_healthie_user_id('1051529') # 1051529 : Omar's "Patient One"

    data_reported = RemoteMonitoringDataReporting(entry['syntrillo_internal_key'])

    # Get pillbox report
    start_date = datetime(2024, 6, 10)
    end_date = datetime.now()
    expected_pattern = "twice daily"
    report, log = data_reported.get_pillbox_report(start_date, end_date, expected_pattern)

    print(report)







