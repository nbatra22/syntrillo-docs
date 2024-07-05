import uuid
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone
import plotly.graph_objs as go
import plotly.io as pio
from typing import Tuple

from syntrillo.remote_monitoring.syntrillo_database_manager import SyntrilloDatabaseManager
from syntrillo.api_tenovi.device_types import DeviceTypes
from syntrillo.api_tenovi.device_measurements import DeviceMeasurements
from syntrillo.pseudonyms_management.lookup_codes_management import LookUpCodesManagement

class DataReportingHeartRate:

    def __init__(self, syntrillo_internal_key : uuid.UUID) -> None:
        """
        Get user level reports from the remote monitoring system on heart rate.

        Based on Tenovi Watch (heart_rate_statistics) and BPM data (pulse, irregular_heartbeat).

        Data from the remote monitoring system is stored in our PHI database

        Args:
            syntrillo_internal_key : uuid.UUID

        Returns:
            None

        """
        self.syntrillo_internal_key = syntrillo_internal_key

        # set up PHI database connection for this user
        self.syntrillo_database_manager = SyntrilloDatabaseManager(syntrillo_internal_key)


    def get_pulse_dataframe(
        self,
        start_date : datetime = None,
        end_date : datetime = None,
        ) -> Tuple[pd.DataFrame, dict]:
        """
        Get BPM report, only pulse data.

        https://tenovi.com/hwi-device-overview/#tenovi-bpm

        https://tenovi.com/bpm/

        Available metrics:
          - pulse : value_1 is the pulse in bpm
          - irregular_heartbeat : value_1=1 (measurement is only sent if an irregular heartbeat is detected)

        Returns a tuple:
            - pandas dataframe with columns: timestamp_local, pulse
            - log : str

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
        pulse_df, log = self.syntrillo_database_manager.get_tenovi_device_metric_data(
            metric_name=DeviceMeasurements.TENOVI_METRICS_BPM_PULSE,
            start_date=start_date,
            end_date=end_date,
        )

        # ---
        # exit if no data : None or empty dataframe
        if pulse_df is None or pulse_df.empty or log['success'] == False:
            overall_log = {
                'success': False,
                'error': 'No BPM pulse data found',
                'log': log,
            }
            return None, overall_log

        # ---
        # rename columns :
        #  - value_1 -> pulse
        #  - value_2 -> drop
        # drop 'device_name' and 'metric_name' columns
        pulse_df = pulse_df.rename(columns={'value_1': 'pulse'})
        pulse_df = pulse_df.drop(columns=['device_name', 'metric_name', 'value_2'])

        # ---
        # make sure pulse is numeric
        pulse_df['pulse'] = pd.to_numeric(pulse_df['pulse'], errors='coerce')

        # ---
        # Convert 'timestamp_local' to datetime objects
        pulse_df['timestamp_local'] = pd.to_datetime(pulse_df['timestamp_local'])

        # ---
        # store the dataframe in the class
        self.pulse_df = pulse_df

        # return the dataframe and the log
        return pulse_df, log

    def get_irregular_heartbeat_dataframe(
        self,
        start_date : datetime = None,
        end_date : datetime = None,
        ) -> Tuple[pd.DataFrame, dict]:
        """
        Get BPM report, only pulse data.

        https://tenovi.com/hwi-device-overview/#tenovi-bpm

        https://tenovi.com/bpm/

        Available metrics:
          - irregular_heartbeat : value_1=1 (measurement is only sent if an irregular heartbeat is detected)

        Returns a tuple:
            - pandas dataframe with columns: timestamp_local, irregular_heartbeat
            - log : str

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
        ihb_df, log = self.syntrillo_database_manager.get_tenovi_device_metric_data(
            metric_name=DeviceMeasurements.TENOVI_METRICS_BPM_IRREGULAR_HEARTBEAT,
            start_date=start_date,
            end_date=end_date,
        )

        # ---
        # exit if no data : None or empty dataframe
        if ihb_df is None or ihb_df.empty or log['success'] == False:
            overall_log = {
                'success': False,
                'error': 'No BPM pulse data found',
                'log': log,
            }
            return None, overall_log

        # ---
        # rename columns :
        #  - value_1 -> irregular_heartbeat
        #  - value_2 -> drop
        # drop 'device_name' and 'metric_name' columns
        ihb_df = ihb_df.rename(columns={'value_1': 'irregular_heartbeat'})
        ihb_df = ihb_df.drop(columns=['device_name', 'metric_name', 'value_2'])

        # ---
        # make sure irregular_heartbeat is numeric
        ihb_df['irregular_heartbeat'] = pd.to_numeric(ihb_df['irregular_heartbeat'], errors='coerce')

        # ---
        # Convert 'timestamp_local' to datetime objects
        ihb_df['timestamp_local'] = pd.to_datetime(ihb_df['timestamp_local'])

        # ---
        # store the dataframe in the class
        self.irregular_heartbeat_df = ihb_df

        # return the dataframe and the log
        return ihb_df, log


    def get_heart_rate_statistics_dataframe(
        self,
        start_date : datetime = None,
        end_date : datetime = None,
        ) -> Tuple[pd.DataFrame, dict]:
        """
        Get Watch report, only heartrate_statistics data.

        https://tenovi.com/hwi-device-overview/#tenovi-watch

        https://tenovi.com/tenovi-smart-watch/

        Available metrics:
            - heart_rate_statistics : value_1 is the hourly_average_pulse in bpm, value_2 is the hourly_max_pulse in bpm

        Returns a tuple:
            - pandas dataframe with columns: timestamp_local, hourly_average_pulse, hourly_maximum_pulse
            - log : str

        """

        # ------------------------------------------------------
        # get data
        #   - make sure start_date and end_date are at midnight
        #   - deal with edges cases


        # ---
        # deal with None start_date, end_date
        if start_date is None:
            first_record, log = self.syntrillo_database_manager.get_first_tenovi_device_data(device_name=DeviceTypes.TENOVI_DEVICE_NAME__WATCH)
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
        heart_rate_statistics_df, log = self.syntrillo_database_manager.get_tenovi_device_metric_data(
            metric_name=DeviceMeasurements.TENOVI_METRICS_WATCH_HEART_RATE_STATISTICS,
            start_date=start_date,
            end_date=end_date,
        )

        # ---
        # exit if no data : None or empty dataframe
        if heart_rate_statistics_df is None or heart_rate_statistics_df.empty or log['success'] == False:
            overall_log = {
                'success': False,
                'error': 'No Watch heart rate stats data found',
                'log': log,
            }
            return None, overall_log

        # ---
        # rename columns :
        #  - value_1 -> pulse
        #  - value_2 -> drop
        # drop 'device_name' and 'metric_name' columns
        heart_rate_statistics_df = heart_rate_statistics_df.rename(columns={'value_1': 'hourly_average_pulse', 'value_2': 'hourly_maximum_pulse'})
        heart_rate_statistics_df = heart_rate_statistics_df.drop(columns=['device_name', 'metric_name'])

        # ---
        # make sure data is numeric
        heart_rate_statistics_df['hourly_average_pulse'] = pd.to_numeric(heart_rate_statistics_df['hourly_average_pulse'], errors='coerce')
        heart_rate_statistics_df['hourly_maximum_pulse'] = pd.to_numeric(heart_rate_statistics_df['hourly_maximum_pulse'], errors='coerce')


        # ---
        # Convert 'timestamp_local' to datetime objects
        heart_rate_statistics_df['timestamp_local'] = pd.to_datetime(heart_rate_statistics_df['timestamp_local'])

        # ---
        # store the dataframe in the class
        self.heart_rate_statistics_df = heart_rate_statistics_df

        # return the dataframe and the log
        return heart_rate_statistics_df, log

    def get_pulse_plotly(
        self,
        representation: str = 'html',
    ):
        """
        Creates a figure from the pulse and irregular_heartrate data.

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
            representation (str): 'html' or 'json'

        Returns a tuple:
            - the figure
            - its representation as html or json

        """

        # ---
        # check if pulse_df data is available
        if not hasattr(self, 'pulse_df'):
            return None, None

        if self.pulse_df is None or self.pulse_df.empty:
            return None, None

        # ---
        # create the figure

        # Define accessible colors for the plot
        pulse_color = 'green'
        irregular_heartrate_color = 'red'

        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                x=self.pulse_df['timestamp_local'],
                y=self.pulse_df['pulse'],
                mode='lines+markers',
                name='Pulse',
                line=dict(color=pulse_color)
                )
            )

        if hasattr(self, 'irregular_heartbeat_df') and self.irregular_heartbeat_df is not None and not self.irregular_heartbeat_df.empty:
            fig.add_trace(
                go.Scatter(
                    x=self.irregular_heartbeat_df['timestamp_local'],
                    y=self.irregular_heartbeat_df['irregular_heartbeat'],
                    mode='markers',
                    name='Irregular heartbeat event',
                    line=dict(color=irregular_heartrate_color)
                    )
                )

        fig.update_layout(
            title='Pulse and Irregular Heartbeat',
            xaxis_title='Date',
            yaxis=dict(title='bpm', side='left'),
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='center', x=0.5),
            )


        # ---
        # convert the figure to html or json
        if representation == 'html':
            representation_output = pio.to_html(fig, full_html=False)
        elif representation == 'json':
            representation_output = json.dumps(fig, cls=pio.PlotlyJSONEncoder)

        # ---
        # return the figure as html or json
        return fig, representation_output


    def get_heart_rate_statistics_plotly(
        self,
        representation: str = 'html',
    ):
        """
        Creates a figure from the watch hourly heart rate stats data.

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
            representation (str): 'html' or 'json'

        Returns a tuple:
            - the figure
            - its representation as html or json

        """

        # ---
        # check if pulse_df data is available
        if not hasattr(self, 'heart_rate_statistics_df'):
            return None, None

        if self.heart_rate_statistics_df is None or self.heart_rate_statistics_df.empty:
            return None, None

        # ---
        # create the figure

        # Define accessible colors for the plot
        hourly_average_pulse = 'blue'
        hourly_maximum_pulse = 'orange'

        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                x=self.heart_rate_statistics_df['timestamp_local'],
                y=self.heart_rate_statistics_df['hourly_average_pulse'],
                mode='markers',
                name='Hourly Average Pulse',
                line=dict(color=hourly_average_pulse)
                )
            )

        fig.add_trace(
            go.Scatter(
                x=self.heart_rate_statistics_df['timestamp_local'],
                y=self.heart_rate_statistics_df['hourly_maximum_pulse'],
                mode='markers',
                name='Hourly Maximum Pulse',
                line=dict(color=hourly_maximum_pulse)
                )
            )

        fig.update_layout(
            title='Hourly heart rate statistics',
            xaxis_title='Date',
            yaxis=dict(title='bpm', side='left'),
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='center', x=0.5),
            )


        # ---
        # convert the figure to html or json
        if representation == 'html':
            representation_output = pio.to_html(fig, full_html=False)
        elif representation == 'json':
            representation_output = json.dumps(fig, cls=pio.PlotlyJSONEncoder)

        # ---
        # return the figure as html or json
        return fig, representation_output


    def get_pulse_moments(
        self,
        start_date : datetime = None,
        end_date : datetime = None,
    ):
        """
        get stat moments of the pulse data: average, std, min, max, median, 25%, 75%, kurtoisis, skewness

        Returns a dictionary with the moments

        """

        # ---
        if not hasattr(self, 'pulse_df') and self.pulse_df is None and not self.pulse_df.empty:
            return None

        # ---
        # get timezone of the first data point
        tz = self.pulse_df['timestamp_local'][0].tzinfo

        # ---
        # filter the data with start_date and end_date
        pulse_df = self.pulse_df.copy()
        if start_date is not None:
            pulse_df = pulse_df[pulse_df['timestamp_local'] >= start_date.replace(tzinfo=tz)]
        if end_date is not None:
            pulse_df = pulse_df[pulse_df['timestamp_local'] <= end_date.replace(tzinfo=tz)]

        # get stats
        moments = self.pulse_df['pulse'].describe().to_dict()

        # add skewness and kurtosis
        moments['skewness'] = self.pulse_df['pulse'].skew()
        moments['kurtosis'] = self.pulse_df['pulse'].kurtosis()

        return moments

    def get_rmssd(
        self,
        start_date : datetime = None,
        end_date : datetime = None,
    ):
        """
        The root mean square of successive differences (RMSSD) is a common HRV measure. Without beat-to-beat data, you can approximate it using the differences between successive hourly averages.

        Process:
            - get the hourly average pulse data
            - get the differences between successive hourly averages
            - square each difference
            - take the mean of the squared differences
            - take the square root

        Args:
            start_date : datetime
            end_date : datetime

        Returns:
            RMSSD value

        """

        # ---
        # check dataframe exists and is not empty
        if not hasattr(self, 'heart_rate_statistics_df') and self.heart_rate_statistics_df is None and not self.heart_rate_statistics_df.empty:
            return None

        # ---
        # get timezone of the first data point
        tz = self.heart_rate_statistics_df['timestamp_local'][0].tzinfo

        # ---
        # filter the data with start_date and end_date
        heart_rate_statistics_df = self.heart_rate_statistics_df.copy()
        if start_date is not None:
            heart_rate_statistics_df = heart_rate_statistics_df[heart_rate_statistics_df['timestamp_local'] >= start_date.replace(tzinfo=tz)]
        if end_date is not None:
            heart_rate_statistics_df = heart_rate_statistics_df[heart_rate_statistics_df['timestamp_local'] <= end_date.replace(tzinfo=tz)]

        # ---
        # get the hourly average pulse data
        hourly_average_pulse = heart_rate_statistics_df[ ['timestamp_local', 'hourly_average_pulse'] ]

        # ---
        # order by ascending timestamp
        hourly_average_pulse = hourly_average_pulse.sort_values(by='timestamp_local')

        # ---
        # get the differences of hourly_average_pulse between successive timestamps
        hourly_average_pulse['diff'] = hourly_average_pulse['hourly_average_pulse'].diff()

        # ---
        # square each difference
        hourly_average_pulse['diff_squared'] = hourly_average_pulse['diff'] ** 2

        # ---
        # take the mean of the squared differences
        mean_squared_diff = hourly_average_pulse['diff_squared'].mean()

        # ---
        # take the square root
        rmssd = np.sqrt(mean_squared_diff)

        return rmssd





if __name__ == '__main__':
# Example usage
    lookup_codes = LookUpCodesManagement()
    entry = lookup_codes.retrieve_entry_by_healthie_user_id('1051529') # 1051529 : Omar's "Patient One" / 1035117 : "Patient One"
    lookup_codes.close_connection()

    # ---
    # get data
    data_reporting_heart_rate = DataReportingHeartRate(entry['syntrillo_internal_key'])

    start_date = datetime.now() - timedelta(days=100)
    end_date = datetime.now()

    pulse_df, log = data_reporting_heart_rate.get_pulse_dataframe(start_date=start_date, end_date=end_date)

    print(pulse_df.head())

    irregular_heartbeat_df, log = data_reporting_heart_rate.get_irregular_heartbeat_dataframe(start_date=start_date, end_date=end_date)

    if irregular_heartbeat_df is not None:
        print(irregular_heartbeat_df.head())

    heart_rate_statistics_df, log = data_reporting_heart_rate.get_heart_rate_statistics_dataframe(start_date=start_date, end_date=end_date)

    if heart_rate_statistics_df is not None:
        print(heart_rate_statistics_df.head())

    pulse_moments = data_reporting_heart_rate.get_pulse_moments(start_date=start_date, end_date=end_date)

    if pulse_moments is not None:
        print(json.dumps(pulse_moments, indent=4, default=str))


    rmssd = data_reporting_heart_rate.get_rmssd(start_date=start_date, end_date=end_date)
    print("rmssd:", rmssd)


