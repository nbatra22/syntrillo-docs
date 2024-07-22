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

class DataReportingBloodPressure:
    """
    Get user level reports from the remote monitoring system on blood pressure.

    Based on Tenovi BPM data.

    Data from the remote monitoring system is stored in our PHI database

    First need to call get dataframe, to prevent several calls.

    Args:
        syntrillo_internal_key : uuid.UUID

    Returns:
        None

    """

    # class variables
    syntrillo_internal_key : uuid.UUID = None
    syntrillo_database_manager : SyntrilloDatabaseManager = None
    bpm_df : pd.DataFrame = None

    # color maps for systolic and diastolic
    alpha : float = 0.5

    no_data_string : str = "no data"

    def __init__(self, syntrillo_internal_key : uuid.UUID) -> None:

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
            - pandas dataframe with columns:
                - timestamp_local: local time to the patient, string type, using datetime isoformat (to prevent any databasing and conversion issue)
                - systolic
                - diastolic
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
        self.bpm_df = bpm_df

        # return the dataframe and the log
        return bpm_df, log


    def get_blood_pressure_plotly(
        self,
        representation: str = 'html',
        html_no_data : str = 'No blood pressure data available',
    ) -> Tuple[go.Figure, str, dict]:
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
            representation (str): 'html' or 'json' or 'both'

        Returns a tuple:
            - the figure
            - its representation as html
            - its representation as json

        """

        # ---
        # check if the data is available
        if self.bpm_df is None or self.bpm_df.empty:
            return None, html_no_data, None

        # ---
        # create the figure

        # Define accessible colors for systolic and diastolic
        systolic_color = '#1f77b4'  # Blue
        diastolic_color = '#ff7f0e'  # Orange

        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                x=self.bpm_df['timestamp_local'],
                y=self.bpm_df['systolic'],
                mode='lines+markers',
                name='systolic',
                line=dict(color=systolic_color)
                )
            )

        fig.add_trace(
            go.Scatter(
                x=self.bpm_df['timestamp_local'],
                y=self.bpm_df['diastolic'],
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
        if self.bpm_df is None or self.bpm_df.empty :
            return None, None

        start_date = self.bpm_df['timestamp_local'].min()
        end_date = self.bpm_df['timestamp_local'].max()

        return start_date, end_date

    def _get_color_for_systolic(self, systolic: float) -> str:
        """
        Function to get color for systolic blood pressure value using a colormap

        Args:
            systolic: float, the systolic blood pressure value

        Returns:
            color: str, the color corresponding to the systolic value
        """
        # Normalize the systolic values to the range of the colormap
        norm_red = mcolors.Normalize(vmin=130, vmax=200)
        norm_green = mcolors.Normalize(vmin=100, vmax=130)

        # Define the colormap
        colormap_red = colormaps['autumn']
        colormap_green = colormaps['summer']

        # Map the systolic value to a color, with a reversed colormap
        z = 0.1
        if systolic >= 130:
            color = (1 - norm_red(systolic)/4, z, z)
        elif 100 <= systolic < 130:
            color = (z, 1-norm_green(systolic)/4, z)
        else:
            # blue
            color = (z, z, 1)

        # Add the alpha transparency
        color_with_alpha = (color[0], color[1], color[2], self.alpha)

        # Convert the RGBA color to a hexadecimal string with alpha
        color_hex = mcolors.to_hex(color_with_alpha, keep_alpha=True)

        return color_hex


    def _get_color_for_diastolic(self, diastolic: float) -> str:
        """
        Function to get color for diastolic blood pressure value using a colormap

        Args:
            diastolic: float, the diastolic blood pressure value

        Returns:
            color: str, the color corresponding to the diastolic value
        """
        norm_red = mcolors.Normalize(vmin=90, vmax=120)
        norm_green = mcolors.Normalize(vmin=50, vmax=90)

        # Define the colormap
        colormap_red = colormaps['autumn']
        colormap_green = colormaps['summer']

        # Map the systolic value to a color, with a reversed colormap
        z = 0.1
        if diastolic >= 90:
            color = (1 - norm_red(diastolic)/4, z, z)
        elif 50 <= diastolic < 90:
            color = (z, 1-norm_green(diastolic)/4, z)
        else:
            # blue
            color = (z, z, 1)

        # Add the alpha transparency
        color_with_alpha = (color[0], color[1], color[2], self.alpha)

        # Convert the RGBA color to a hexadecimal string with alpha
        color_hex = mcolors.to_hex(color_with_alpha, keep_alpha=True)

        return color_hex

    def _get_color_for_percent_above_130_90(self, percent_above_130_90: float) -> str:
        """
        Function to get color for percent of blood pressure values above 130/90 using a colormap

        Args:
            percent_above_130_90: float, the percentage of blood pressure values above 130/90

        Returns:
            color: str, the color corresponding to the percentage of values above 130/90
        """
        # Normalize the percentage values to the range of the colormap
        norm = mcolors.Normalize(vmin=0, vmax=100)

        # Define the colormap
        #  get all colormaps with list(colormaps)
        colormap = colormaps['autumn']

        # Map the systolic value to a color, with a reversed colormap
        if percent_above_130_90 == 0:
            # color is green
            color = (0, 1, 0)
        else:
            # it is yellow to red
            color = colormap(1 - norm(percent_above_130_90))

        # Add the alpha transparency
        color_with_alpha = (color[0], color[1], color[2], self.alpha)

        # Convert the RGBA color to a hexadecimal string with alpha
        color_hex = mcolors.to_hex(color_with_alpha, keep_alpha=True)

        return color_hex


    def _calculate_summary_for_a_date_range_row(self, row) -> pd.Series:
        """
        Function to calculate summary statistics for a given date range

        Args:
            row : pd.Series with columns from_date, to_date, range_name

        Returns:
            pd.Series with columns:
                - from_date
                - to_date
                - range_name
                - num_datapoints_bp
                - systolic_min
                - systolic_max
                - systolic_mean
                - systolic_median
                - diastolic_min
                - diastolic_max
                - diastolic_mean
                - diastolic_median
                - num_above_130_90 ( SBP ge 140 OR DBP ge 90)
                - percent_above_130_90
                - systolic_mean_color
                - diastolic_mean_color
                - percent_above_130_90_color
        """
        from_date = row['from_date']
        to_date = row['to_date']
        range_name = row['range_name']

        # Filter blood pressure data for the current date range
        filtered_bp = self.bpm_df[(self.bpm_df['timestamp_local'] >= from_date) &
                                  (self.bpm_df['timestamp_local'] <= to_date)]

        num_datapoints_bp = len(filtered_bp)

        if num_datapoints_bp == 0:
            systolic_min = systolic_max = systolic_mean = systolic_median = self.no_data_string
            diastolic_min = diastolic_max = diastolic_mean = diastolic_median = self.no_data_string
            num_above_130_90 = percent_above_130_90 = self.no_data_string
            systolic_mean_color = diastolic_mean_color = percent_above_130_90_color = "white"
        else:
            systolic_min = filtered_bp['systolic'].min()
            systolic_max = filtered_bp['systolic'].max()
            systolic_mean = filtered_bp['systolic'].mean()
            systolic_median = filtered_bp['systolic'].median()

            diastolic_min = filtered_bp['diastolic'].min()
            diastolic_max = filtered_bp['diastolic'].max()
            diastolic_mean = filtered_bp['diastolic'].mean()
            diastolic_median = filtered_bp['diastolic'].median()

            above_140_90 = filtered_bp[(filtered_bp['systolic'] >= 130) | (filtered_bp['diastolic'] >= 90)]
            num_above_130_90 = len(above_140_90)
            percent_above_130_90 = (num_above_130_90 / num_datapoints_bp) * 100

            # Add a color column to the filtered blood pressure data
            systolic_mean_color = self._get_color_for_systolic(systolic_mean)
            diastolic_mean_color = self._get_color_for_diastolic(diastolic_mean)
            percent_above_130_90_color = self._get_color_for_percent_above_130_90(percent_above_130_90)


        return pd.Series({
            'from_date': from_date,
            'to_date': to_date,
            'range_name': range_name,
            'num_datapoints_bp': num_datapoints_bp,
            'systolic_min': systolic_min,
            'systolic_max': systolic_max,
            'systolic_mean': systolic_mean,
            'systolic_median': systolic_median,
            'diastolic_min': diastolic_min,
            'diastolic_max': diastolic_max,
            'diastolic_mean': diastolic_mean,
            'diastolic_median': diastolic_median,
            'num_above_130_90': num_above_130_90,
            'percent_above_130_90': percent_above_130_90,
            'systolic_mean_color': systolic_mean_color,
            'diastolic_mean_color': diastolic_mean_color,
            'percent_above_130_90_color': percent_above_130_90_color,
        })

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
                - systolic_min
                - systolic_max
                - systolic_mean
                - systolic_median
                - diastolic_min
                - diastolic_max
                - diastolic_mean
                - diastolic_median
                - num_above_130_90 ( SBP ge 140 OR DBP ge 90)
                - percent_above_130_90
                - systolic_mean_color
                - diastolic_mean_color
                - percent_above_130_90_color
            - log : dict with success and error message

        """

        # check if some data is available
        if self.bpm_df is None or self.bpm_df.empty:
            return None, {
                'success': False,
                'error': 'No blood pressure data available',
            }

        # get the summary statistics for each date range
        try:
            summary_stats = date_ranges.apply(self._calculate_summary_for_a_date_range_row, axis=1)

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




if __name__ == '__main__':
# Example usage
    lookup_codes = LookUpCodesManagement()
    entry = lookup_codes.retrieve_entry_by_healthie_user_id('1035117') # 1051529 : Omar's "Patient One" / 1035117 : "Patient One"
    lookup_codes.close_connection()

    # ---
    # get data
    data_reporting_blood_pressure = DataReportingBloodPressure(entry['syntrillo_internal_key'])

    if False:
        start_date = datetime.now() - timedelta(days=30)
        end_date = datetime.now()
    else:
        start_date = None
        end_date = None

    bpm_data, log = data_reporting_blood_pressure.get_blood_pressure_dataframe(
        start_date=start_date,
        end_date=end_date,
    )

    print(log)

    # print the first 5 rows of the dataframe
    print(bpm_data.head())

    # ---
    if False:
    # get the plot as html
        fig, output, _ = data_reporting_blood_pressure.get_blood_pressure_plotly(
            representation='html'
        )

        # print the first chars of output
        print(output[:100])

    # ---
    if False:
        # print date range
        from_date, to_date = data_reporting_blood_pressure.get_date_range()
        print(from_date, to_date)

    if True:
        color = data_reporting_blood_pressure._get_color_for_percent_above_130_90(0)
        print(color)
        color = data_reporting_blood_pressure._get_color_for_percent_above_130_90(50)
        print(color)
        color = data_reporting_blood_pressure._get_color_for_percent_above_130_90(100)
        print(color)

    pass
