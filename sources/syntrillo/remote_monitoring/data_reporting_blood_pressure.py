import uuid
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone
import plotly.graph_objs as go
import plotly.io as pio
import plotly.utils as pu
from typing import Tuple

from syntrillo.remote_monitoring.syntrillo_database_manager import SyntrilloDatabaseManager
from syntrillo.api_tenovi.device_types import DeviceTypes
from syntrillo.api_tenovi.device_measurements import DeviceMeasurements
from syntrillo.pseudonyms_management.lookup_codes_management import LookUpCodesManagement

class DataReportingBloodPressure:

    def __init__(self, syntrillo_internal_key : uuid.UUID) -> None:
        """
        Get user level reports from the remote monitoring system on blood pressure.

        Based on Tenovi BPM data.

        Data from the remote monitoring system is stored in our PHI database

        Args:
            syntrillo_internal_key : uuid.UUID

        Returns:
            None

        """
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
            - pandas dataframe with columns: timestamp_local, systolic, diastolic
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
        self.bmp_df = bpm_df

        # return the dataframe and the log
        return bpm_df, log


    def get_blood_pressure_plotly(
        self,
        representation: str = 'html'
    ):
        """
        Creates a figure from the blood pressure data.

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
        # check if the data is available
        if not hasattr(self, 'bmp_df'):
            return None, None

        if self.bmp_df is None or self.bmp_df.empty:
            return None, None

        # ---
        # create the figure

        # Define accessible colors for systolic and diastolic
        systolic_color = '#1f77b4'  # Blue
        diastolic_color = '#ff7f0e'  # Orange

        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                x=self.bmp_df['timestamp_local'],
                y=self.bmp_df['systolic'],
                mode='lines+markers',
                name='systolic',
                line=dict(color=systolic_color)
                )
            )

        fig.add_trace(
            go.Scatter(
                x=self.bmp_df['timestamp_local'],
                y=self.bmp_df['diastolic'],
                mode='lines+markers',
                name='diastolic',
                line=dict(color=diastolic_color)
                )
            )

        fig.update_layout(
            title='Blood Pressure',
            xaxis_title='Date',
            yaxis=dict(title='Blood Pressure (mmHg)', side='left'),
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='center', x=0.5),
            )


        # ---
        # convert the figure to html or json
        if representation == 'html':
            representation_output = pio.to_html(fig, full_html=False)
        elif representation == 'json':
            representation_output = json.dumps(fig, cls=pu.PlotlyJSONEncoder)

        # ---
        # return the figure as html or json
        return fig, representation_output



if __name__ == '__main__':
# Example usage
    lookup_codes = LookUpCodesManagement()
    entry = lookup_codes.retrieve_entry_by_healthie_user_id('1051529') # 1051529 : Omar's "Patient One" / 1035117 : "Patient One"
    lookup_codes.close_connection()

    # ---
    # get data
    data_reporting_blood_pressure = DataReportingBloodPressure(entry['syntrillo_internal_key'])

    start_date = datetime.now() - timedelta(days=30)
    end_date = datetime.now()

    bpm_data, log = data_reporting_blood_pressure.get_blood_pressure_dataframe(
        start_date=start_date,
        end_date=end_date,
    )

    print(log)

    # print the first 5 rows of the dataframe
    print(bpm_data.head())

    fig, output = data_reporting_blood_pressure.get_blood_pressure_plotly(
        representation='html'
    )

    # print the first chars of output
    print(output[:100])

