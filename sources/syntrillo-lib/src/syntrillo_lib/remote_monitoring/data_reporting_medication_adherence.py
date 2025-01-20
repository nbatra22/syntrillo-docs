# Path: ./sources/syntrillo/remote_monitoring/data_reporting_medication_adherence.py
import uuid
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone

from syntrillo_lib.system.matplotlib_setup import setup_matplotlib
setup_matplotlib()

import matplotlib
import matplotlib.cm as cm # color map

from syntrillo_lib.remote_monitoring.syntrillo_database_manager import SyntrilloDatabaseManager
from syntrillo_lib.api_tenovi.device_types import DeviceTypes
from syntrillo_lib.pseudonyms_management.lookup_codes_management import LookUpCodesManagement

class DataReportingMedicationAdherence:

    def __init__(self, syntrillo_internal_key : uuid.UUID) -> None:
        """
        Get user level reports from the remote monitoring system on medication adherence.

        Based on Tenovi Pillbox data.

        Data from the remote monitoring system is stored in our PHI database

        Args:
            syntrillo_internal_key : uuid.UUID

        Returns:
            None

        """
        self.syntrillo_internal_key = syntrillo_internal_key

        # set up PHI database connection for this user
        self.syntrillo_database_manager = SyntrilloDatabaseManager(syntrillo_internal_key)


    def get_pillbox_detailed_report(
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

        Returns a tuple:
            - report : dict
            - log : str

        """

        # ------------------------------------------------------
        # get data
        #   - make sure start_date and end_date are at midnight
        #   - deal with edges cases


        # ---
        # deal with None start_date, end_date
        if start_date is None:
            first_record, log = self.syntrillo_database_manager.get_first_tenovi_device_data(device_name=DeviceTypes.TENOVI_DEVICE_NAME__PILLBOX)
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
        # get pillbox data from PHI database, ordered by timestamp
        pillbox_data, log = self.syntrillo_database_manager.get_tenovi_device_data(
            device_name=DeviceTypes.TENOVI_DEVICE_NAME__PILLBOX,
            start_date=start_date,
            end_date=end_date,
        )

        # ---
        # exit if no pillbox data : None or empty dataframe
        if pillbox_data is None or pillbox_data.empty or log['success'] == False:
            overall_log = {
                'success': False,
                'error': 'No pillbox data found',
                'log': log,
            }
            return None, overall_log

        # ------------------------------------------------------
        # get total number of pillbox_refilled events, if any
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

        # get pillbox_opened events
        pillbox_opened = pillbox_data[pillbox_data['metric_name'] == 'pillbox_opened']

        # ------------------------------------------------------
        # create a new panda dataframe with 7 rows (one for each day of the week) and several sets of AM, PM columns with:
        #  - actual count of pillbox_opened events
        #  - expected count of pillbox_opened events
        #  - difference between actual and expected
        #  - ratio of actual to expected
        #  - color representing the ratio, differences and potential issues
        pillbox_opened_status_per_day_df = pd.DataFrame(
            np.zeros((7, 2*8)),
            columns=[
                'AM_actual_raw', 'PM_actual_raw',  # with duplicates
                'AM_actual', 'PM_actual',          # without duplicates
                'AM_expected', 'PM_expected',
                'AM_diff', 'PM_diff',
                'AM_ratio', 'PM_ratio',
                'AM_color', 'PM_color',
                'AM_comment', 'PM_comment',
                'AM_data', 'PM_data',
                ]
            )

        row_names = ['sun', 'mon', 'tue', 'wed', 'thu', 'fri', 'sat']
        pillbox_opened_status_per_day_df.index = row_names

        # Converting columns to the desired types
        pillbox_opened_status_per_day_df = pillbox_opened_status_per_day_df.astype({
            'AM_actual_raw': 'int32',
            'PM_actual_raw': 'int32',
            'AM_actual': 'int32',
            'PM_actual': 'int32',
            'AM_expected': 'int32',
            'PM_expected': 'int32',
            'AM_diff': 'int32',
            'PM_diff': 'int32',
            'AM_ratio': 'float64',
            'PM_ratio': 'float64',
            'AM_color': 'str',
            'PM_color': 'str',
            'AM_comment': 'str',
            'PM_comment': 'str',
            'AM_data': 'str',
            'PM_data': 'str',
        })

        # ------------------------------------------------------
        # get actual count of pillbox_opened events
        current_row_date = None
        current_am_pm = None
        duplicate_count = 0
        for index, row in pillbox_opened.iterrows():
            # get date from row['timestamp_local'], which has this isoformat: '2024-06-26T15:43:08.000000-04:00'
            row_date = datetime.strptime(row['timestamp_local'], '%Y-%m-%dT%H:%M:%S.%f%z').date()
            day_of_week = int(round(float(row['value_1']), 0)) - 1
            am_pm = int(round(float(row['value_2']), 0)) - 1 # columns 0 and 1 for AM_actual and PM_actual
            if row_date == current_row_date and am_pm == current_am_pm:
                duplicate_count += 1
                pillbox_opened_status_per_day_df.iloc[day_of_week, am_pm] += 1 # raw, with duplicates
                continue
            pillbox_opened_status_per_day_df.iloc[day_of_week, am_pm] += 1 # raw, with duplicates
            pillbox_opened_status_per_day_df.iloc[day_of_week, am_pm + 2] += 1  # without duplicates
            current_row_date = row_date
            current_am_pm = am_pm

        # ------------------------------------------------------
        # build expected df from the expected pattern

        # loop for each day from start_date to end_date :
        # add 1 to the expected df for each day and AM/PM that matches the expected pattern
        current_day = start_date.date()
        while current_day <= end_date.date():
            # get day of the week
            day_of_week = current_day.weekday() + 1 if current_day.weekday() < 6 else 0
            # get expected AM/PM from expected pattern
            if expected_pattern == "twice daily":
                pillbox_opened_status_per_day_df.iloc[day_of_week, 4] += 1
                pillbox_opened_status_per_day_df.iloc[day_of_week, 5] += 1
            elif expected_pattern == "daily AM":
                pillbox_opened_status_per_day_df.iloc[day_of_week, 4] += 1
            elif expected_pattern == "daily PM":
                pillbox_opened_status_per_day_df.iloc[day_of_week, 5] += 1
            current_day += timedelta(days=1)


        # ------------------------------------------------------
        # add a row that sums up the columns
        pillbox_opened_status_per_day_df.loc['total'] = pillbox_opened_status_per_day_df.sum()

        # ------------------------------------------------------
        # compare actual and expected

        # get total number of actual doses : that's the sum of all cells in pillbox_opened_status_per_day_df AM_actual and PM_actual columns
        actual_doses = pillbox_opened_status_per_day_df['AM_actual'].sum() + pillbox_opened_status_per_day_df['PM_actual'].sum()

        # get total number of expected doses : that's the sum of all cells in pillbox_opened_status_per_day_df AM_expected and PM_expected columns
        expected_doses = pillbox_opened_status_per_day_df['AM_expected'].sum() + pillbox_opened_status_per_day_df['PM_expected'].sum()

        # get number of missed doses : that's the difference between expected and actual doses
        missed_doses = expected_doses - actual_doses

        # calculate differences  (expected - actual) in pillbox_opened_status_per_day_df AM_diff and PM_diff columns
        #  : useful to detect negative numbers, which would indicate that the patient took more doses than expected or at the wrong time
        pillbox_opened_status_per_day_df['AM_diff'] = pillbox_opened_status_per_day_df['AM_expected'] - pillbox_opened_status_per_day_df['AM_actual']
        pillbox_opened_status_per_day_df['PM_diff'] = pillbox_opened_status_per_day_df['PM_expected'] - pillbox_opened_status_per_day_df['PM_actual']

        # calculate ratio  (actual/expected) in pillbox_opened_status_per_day_df AM_ratio and PM_ratio columns
        pillbox_opened_status_per_day_df['AM_ratio'] = pillbox_opened_status_per_day_df['AM_actual'] / pillbox_opened_status_per_day_df['AM_expected']
        pillbox_opened_status_per_day_df['PM_ratio'] = pillbox_opened_status_per_day_df['PM_actual'] / pillbox_opened_status_per_day_df['PM_expected']

        # ------------------------------------------------------
        # determine colors and comments based on diff and ratio
        #  - green to red colormap: 0% to 100% missed doses
        #  - black : a negative number, which would indicate that the patient took more doses than expected or at the wrong time
        #  - white : no expected dosage
        #  - use matplotlib to display the dataframe with colors

        # initialize color columns to white
        pillbox_opened_status_per_day_df['AM_color'] = 'white'
        pillbox_opened_status_per_day_df['PM_color'] = 'white'

        # initialize comment columns to empty string
        pillbox_opened_status_per_day_df['AM_comment'] = ''
        pillbox_opened_status_per_day_df['PM_comment'] = ''

        # Create a colormap object
        colormap = matplotlib.cm.RdYlGn

        # loop through the dataframe and set colors and comments
        for col_prefix in ['AM', 'PM']:
            for index, row in pillbox_opened_status_per_day_df.iterrows():
                # add data to the AM_data and PM_data columns : actual_raw and expected for AM and PM, line separated with '<br>
                pillbox_opened_status_per_day_df.at[index, col_prefix + '_data'] = col_prefix \
                    + ' : Actual raw: ' \
                    + str(row[col_prefix + '_actual_raw']) \
                    + ' / Expected: ' + str(row[col_prefix + '_expected'])

                # ---
                # color and comment logic
                if row[col_prefix + '_expected'] > 0: # if AM_expected is not zero, then set color based on ratio

                    if row[col_prefix + '_actual_raw'] <= row[col_prefix + '_expected'] : # within expected range

                        ratio = row[col_prefix + '_ratio']
                        # use a green to red colormap with matplotlib: 0% to 100% missed doses
                        color = colormap(ratio)

                        # Convert the color to hex and set it in the DataFrame
                        pillbox_opened_status_per_day_df.at[index, col_prefix + '_color'] = matplotlib.colors.rgb2hex(color[:3])

                        # add adherence comment based on ratio
                        if ratio == 1.0:
                            pillbox_opened_status_per_day_df.at[index, col_prefix + '_comment'] = 'Perfect adherence'
                        elif ratio >= 0.5:
                            pillbox_opened_status_per_day_df.at[index, col_prefix + '_comment'] = 'Partial adherence'
                        else:
                            pillbox_opened_status_per_day_df.at[index, col_prefix + '_comment'] = 'Poor adherence'

                    else: # overdose
                        pillbox_opened_status_per_day_df.at[index, col_prefix + '_color'] = 'violet'
                        pillbox_opened_status_per_day_df.at[index, col_prefix + '_comment'] = 'Pillbox opened more than expected'

                # if expected==0 and actual_raw is greater than zero, the patient took doses that were not expected
                if row[col_prefix + '_expected']==0 and row[col_prefix + '_actual_raw'] > 0:
                    pillbox_opened_status_per_day_df.at[index, col_prefix + '_color'] = 'black'
                    pillbox_opened_status_per_day_df.at[index, col_prefix + '_comment'] = 'Pillbox opening not expected'

        report = {
            'pillbox_refilled_count': pillbox_refilled_count,
            'pillbox_refill_initiated_count': pillbox_refill_initiated_count,
            'missed_doses': missed_doses,
            'duplicate_count': duplicate_count,
            'pillbox_opened_status_per_day_df': pillbox_opened_status_per_day_df,
        }

        return report, log

    def pillbox_global_report(
        self,
        expected_pattern : str = "twice daily",
    ):
        """
        Report medication adherence using all available pillbox information for this patient.

        The report is divided by periods of 7 days, or 28 days, depending on how long the patient has been using the pillbox.

        The report is a dict that includes for each period:
            - date range
            - from the report from get_pillbox_detailed_report(), as a dict, for each day and AM/PM:
                - color
                - data
                - comment

        Args:
            expected_pattern : str = "twice daily", "daily AM", "daily PM"

        Returns a tuple:
            - report : dict
            - log : str
        """

        # -----  get global date range ---------

        # get data of first pillbox event
        first_record, log = self.syntrillo_database_manager.get_first_tenovi_device_data(device_name=DeviceTypes.TENOVI_DEVICE_NAME__PILLBOX)

        if first_record is None:
            log = {
                'success': False,
                'error': 'No pillbox data found',
            }
            return None, log

        date_first_record = datetime.strptime(first_record['timestamp_local'], '%Y-%m-%dT%H:%M:%S.%f%z')

        # add one day and set time to midnight
        date_first_record = date_first_record + timedelta(days=1)
        date_first_record = date_first_record.replace(hour=0, minute=0, second=0, microsecond=0)

        # Get todays date and time as an offset-aware datetime object
        todays_date = datetime.now(date_first_record.tzinfo)

        # remove one day from todays date and set time to midnight
        todays_date = todays_date - timedelta(days=1)
        todays_date = todays_date.replace(hour=0, minute=0, second=0, microsecond=0)

        # ----- get period size : month or week, depending on total number of days -------
        #  - if total number of days is less than 28, use 7 days period
        #  - if total number of days is 28 or more, use 28 days period
        total_number_of_days = (todays_date - date_first_record).days
        if total_number_of_days < 28:
            period_size = 7
            period_label = 'Week'
        else:
            period_size = 28
            period_label = 'Month'

        # loop for each 7 days period from date_first_record to today
        current_date = date_first_record
        global_report = []
        i=1
        while current_date <= todays_date:

            # set start_date and end_date for this period
            start_date = current_date
            end_date = start_date + timedelta(days=period_size - 1) # -1 to avoid overlap with next period
            if end_date > todays_date:
                end_date = todays_date

            # get report for this period
            report, log = self.get_pillbox_detailed_report(start_date, end_date, expected_pattern)

            if report is None:
                # exit while loop
                break

            # get the dataframe
            pillbox_opened_status_per_day_df = report['pillbox_opened_status_per_day_df']

            # extract what we need from the dataframe
            status_per_day = {}
            for index, row in pillbox_opened_status_per_day_df.iterrows():
                status_per_day[index] = {
                    'AM_color': row['AM_color'],
                    'AM_data': row['AM_data'],
                    'AM_comment': row['AM_comment'],
                    'PM_color': row['PM_color'],
                    'PM_data': row['PM_data'],
                    'PM_comment': row['PM_comment'],
                }

            # add the report to the global report
            global_report.append(
                {
                'i': i,
                'name': f'{period_label} {i}',
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'pillbox_refilled_count': report['pillbox_refilled_count'],
                'pillbox_refill_initiated_count': report['pillbox_refill_initiated_count'],
                'missed_doses': report['missed_doses'],
                'duplicate_count': report['duplicate_count'],
                'status_per_day': status_per_day,
                }
            )

            # increment current_date by period_size days
            current_date += timedelta(days=period_size)
            i += 1

        log = {
            'success': True,  # TODO combine logs from all periods
        }

        return global_report, log




if __name__ == "__main__":
    # Example usage
    lookup_codes = LookUpCodesManagement()
    entry = lookup_codes.retrieve_entry_by_healthie_user_id('1051529') # 1051529 : Omar's "Patient One" / PO: 1035117

    data_reported = DataReportingMedicationAdherence(entry['syntrillo_internal_key'])

    if True:
        # Get single pillbox report
        start_date = datetime.now() - timedelta(days=7)
        end_date = datetime.now()
        expected_pattern = "twice daily"
        # expected_pattern = "daily AM"
        report, log = data_reported.get_pillbox_detailed_report(start_date, end_date, expected_pattern)

        print(report)
        print("")
        print(report['pillbox_opened_status_per_day_df'])

    if False:
        # Get global pillbox report
        expected_pattern = "twice daily"
        report, log = data_reported.pillbox_global_report(expected_pattern)

        print(json.dumps(report, indent=4, default=str))












