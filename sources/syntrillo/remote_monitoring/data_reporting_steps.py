import uuid
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone
import plotly.graph_objs as go
import plotly.io as pio
import plotly.utils as pu
from typing import Tuple

import matplotlib.cm as cm
import matplotlib.colors as mcolors
from matplotlib import colormaps

from syntrillo.remote_monitoring.syntrillo_database_manager import SyntrilloDatabaseManager
from syntrillo.api_tenovi.device_types import DeviceTypes
from syntrillo.api_tenovi.device_measurements import DeviceMeasurements
from syntrillo.pseudonyms_management.lookup_codes_management import LookUpCodesManagement

from syntrillo.helper_functions.plotly import plotly_fig_to_dict

# Set a default template
pio.templates.default = "plotly"

class DataReportingSteps:
    """
    Get user level reports from the remote monitoring system on number of stepŝ.

    Based on Tenovi Watch data.

    Data from the remote monitoring system is stored in our PHI database

    First need to call get dataframe, to prevent several DB calls.

    Args:
        syntrillo_internal_key : uuid.UUID

    Returns:
        None

    """

    # class variables
    syntrillo_internal_key : uuid.UUID = None
    syntrillo_database_manager : SyntrilloDatabaseManager = None
    hourly_steps_df : pd.DataFrame = None

    # color maps for systolic and diastolic
    alpha : float = 0.5

    # no data string
    no_data_string : str = "no data"


    def __init__(self, syntrillo_internal_key : uuid.UUID) -> None:

        self.syntrillo_internal_key = syntrillo_internal_key

        # set up PHI database connection for this user
        self.syntrillo_database_manager = SyntrilloDatabaseManager(syntrillo_internal_key)


    def get_hourly_and_daily_steps_dataframes(
        self,
        start_date : datetime = None,
        end_date : datetime = None,
        ) -> Tuple[pd.DataFrame, dict]:
        """
        Get BPM report, only Steps data.

        https://tenovi.com/hwi-device-overview/#tenovi-watch

        https://tenovi.com/tenovi-smart-watch/

        Steps and Heart Rate Statistics are logged in hourly bins. The measurement timestamp will indicate the start of the relevant logging period.

        Available metrics:
          - steps : value_1 is Hourly Steps, value_2 is N/A

        Returns a tuple:
            - pandas dataframe with columns:
                - timestamp_local: local time to the patient, string type, using datetime isoformat (to prevent any databasing and conversion issue)
                - hourly_steps
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
        hourly_steps_df, log = self.syntrillo_database_manager.get_tenovi_device_metric_data(
            metric_name=DeviceMeasurements.TENOVI_METRICS_WATCH_STEPS,
            start_date=start_date,
            end_date=end_date,
        )

        # ---
        # exit if no data : None or empty dataframe
        if hourly_steps_df is None or hourly_steps_df.empty or log['success'] == False:
            overall_log = {
                'success': False,
                'error': 'No BPM blood_pressure data found',
                'log': log,
            }
            return None, overall_log

        # ---
        # rename columns :
        #  - value_1 -> hourly_steps
        #  - value_2 -> N/A ! drop
        # drop 'device_name' and 'metric_name' columns
        hourly_steps_df = hourly_steps_df.rename(columns={'value_1': 'hourly_steps'})
        hourly_steps_df = hourly_steps_df.drop(columns=['device_name', 'metric_name', 'value_2'])

        # ---
        # make sure hourly_steps is numeric
        hourly_steps_df['hourly_steps'] = pd.to_numeric(hourly_steps_df['hourly_steps'], errors='coerce')

        # ---

        # store the dataframe in the class
        self.hourly_steps_df = hourly_steps_df

        # ---
        daily_steps_df = self.get_daily_steps_dataframe()

        # return the dataframe and the log
        return hourly_steps_df, daily_steps_df, log


    def get_daily_steps_dataframe(self):
        """
        Get daily steps dataframe from hourly steps dataframe.

        Returns:
            pd.DataFrame with columns:
                - timestamp_local
                - daily_steps
        """
        if self.hourly_steps_df is None or self.hourly_steps_df.empty:
            return None

        # ---
        # group by date
        daily_steps_df = self.hourly_steps_df.groupby(
            pd.Grouper(key='timestamp_local', freq='D')
        ).agg(
            daily_steps=pd.NamedAgg(column='hourly_steps', aggfunc='sum')
        ).reset_index()

        self.daily_steps_df = daily_steps_df

        return daily_steps_df


    def get_daily_steps_plotly(
        self,
        representation: str = 'html',
        html_no_data : str = 'No steps data available',
    ) -> Tuple[go.Figure, str, dict]:
        """
        Creates a figure from the daily steps data.

        Use HTML for simplicity and direct embedding, and JSON for flexibility and dynamic client-side manipulation.

        Include this in the HTML head: <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>

        Usage if JSON:
            <div id="plot"></div>
            <script type="text/javascript">
                var graphJSON = {{ graph_json|safe }};
                Plotly.newPlot('plot', graphJSON.data, graphJSON.layout);
            </script>

        Usage if HTML:
            <div>
                {{ graph_html|safe }}
            </div>

        Args:
            representation (str): 'html' or 'json' or 'both'

        Returns a tuple:
            - the figure
            - its representation as html
            - its representation as json

        """

        # ---
        # check if the data is available
        if self.daily_steps_df is None or self.daily_steps_df.empty:
            return None, html_no_data, None

        # ---
        # create the figure

        # Define accessible colors for systolic and diastolic
        steps_color = '#1f77b4'  # Blue

        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                x=self.daily_steps_df['timestamp_local'],
                y=self.daily_steps_df['daily_steps'],
                mode='lines+markers',
                name='daily_steps',
                line=dict(color=steps_color)
                )
            )

        fig.update_layout(
            title='Daily Steps',
            xaxis_title='Date',
            yaxis=dict(title='Daily Steps', side='left'),
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='center', x=0.5),
            )


        # ---
        # convert the figure to html or json
        if representation == 'html' or representation == 'both':
            representation_output_html = pio.to_html(fig, full_html=False)
            representation_output_json = None
        elif representation == 'json' or representation == 'both':
            representation_output_json = plotly_fig_to_dict(fig)
            representation_output_html = None
        else:
            representation_output_html = None
            representation_output_json = None

        # ---
        # return the figure as html or json
        return fig, representation_output_html, representation_output_json

    def get_date_range(self) -> Tuple[datetime, datetime]:
        """
        Get the date range of the data.

        Returns:
            start_date : datetime
            end_date : datetime

        """
        if self.hourly_steps_df is None or self.hourly_steps_df.empty :
            return None, None

        start_date = self.hourly_steps_df['timestamp_local'].min()
        end_date = self.hourly_steps_df['timestamp_local'].max()

        return start_date, end_date


    def get_summary_for_a_date_range_row(self, row) -> dict:
        """
        Function to calculate summary statistics for a given date range

        Args:
            row : pd.Series with columns from_date, to_date, range_name

        Returns:
            dict with keys:
                - from_date
                - to_date
                - range_name
                - num_datapoints_steps
                - daily_steps_average
        """
        from_date = row['from_date']
        to_date = row['to_date']
        range_name = row['range_name']

        # Filter blood pressure data for the current date range
        filtered_daily_steps = self.daily_steps_df[(self.daily_steps_df['timestamp_local'] >= from_date) &
                                  (self.daily_steps_df['timestamp_local'] <= to_date)]

        num_datapoints_bp = len(filtered_daily_steps)

        # Calculate summary statistics for the blood pressure data
        if num_datapoints_bp == 0:
            daily_steps_average = None
        else:
            daily_steps_average = filtered_daily_steps['daily_steps'].mean()

        return {
            'from_date': from_date,
            'to_date': to_date,
            'range_name': range_name,
            'num_datapoints_bp': num_datapoints_bp,
            'daily_steps_average': daily_steps_average,
        }


    def get_summary_for_date_ranges(
        self,
        date_ranges : pd.DataFrame,
        ) -> Tuple[ pd.DataFrame, dict]:
        """
        From the blood pressure data, calculate summary statistics for each date range.

        Args:
            date_ranges : pd.DataFrame with columns from_date, to_date, range_name

        Returns:
            - summary_stats : pd.DataFrame with columns:
                - from_date
                - to_date
                - range_name
                - num_datapoints_bp
                - daily_steps_average
            - log : dict with success and error message

        """

        # check if some data is available
        if self.daily_steps_df is None or self.daily_steps_df.empty:
            return None, {
                'success': False,
                'error': 'No blood pressure data available',
            }

        # get the summary statistics for each date range
        try:
            summary_stats_dict = date_ranges.apply(self.get_summary_for_a_date_range_row, axis=1)
            summary_stats = pd.DataFrame(summary_stats_dict.tolist())

        except Exception as e:
            return None, {
                'success': False,
                'error': f'Error calculating summary statistics in get_summary_for_date_ranges',
                'exception': str(e),
            }

        # store the summary statistics and return
        self.summary_stats = summary_stats
        self.date_ranges = date_ranges
        return summary_stats, {
            'success': True,
            'message': 'Summary statistics calculated successfully',
        }

    def get_report_information(self) -> dict:
            """
            Retrieves the report information for blood pressure data.

            Returns:
                A dictionary containing the report information:
                - 'general':
            """
            info = {
                'general' : 'Average of number of daily steps from Tenovi Watch device',
            }

            return info


if __name__ == '__main__':
# Example usage
    lookup_codes = LookUpCodesManagement()
    entry = lookup_codes.retrieve_entry_by_healthie_user_id('1035117') # 1051529 : Omar's "Patient One" / 1035117 : "Patient One"
    lookup_codes.close_connection()

    # ---
    # get data
    data_reporting_steps = DataReportingSteps(entry['syntrillo_internal_key'])

    if False:
        start_date = datetime.now() - timedelta(days=30)
        end_date = datetime.now()
    else:
        start_date = None
        end_date = None

    hourly_steps_data, log = data_reporting_steps.get_hourly_and_daily_steps_dataframes(
        start_date=start_date,
        end_date=end_date,
    )

    daily_steps_data = data_reporting_steps.daily_steps_df

    print(log)

    # print the first 5 rows of the dataframe
    print(hourly_steps_data.head())
    print(daily_steps_data.head())

    if True:

        from_date, to_date = data_reporting_steps.get_date_range()

        # Define the date ranges
        date_ranges = pd.DataFrame({
            'from_date': [from_date, from_date + timedelta(days=7), from_date + timedelta(days=14)],
            'to_date': [from_date + timedelta(days=6), from_date + timedelta(days=13), to_date],
            'range_name': ['Week 1', 'Week 2', 'Week 3'],
        })

        df = data_reporting_steps.get_summary_for_date_ranges(date_ranges)
        print(df)

    pass
