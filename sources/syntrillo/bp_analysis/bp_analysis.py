import uuid
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone
import plotly.graph_objs as go
import plotly.io as pio
import plotly.utils as pu
from typing import Tuple

from syntrillo.system.matplotlib_setup import setup_matplotlib
setup_matplotlib()

import matplotlib.cm as cm
import matplotlib.colors as mcolors
from matplotlib import colormaps

from syntrillo.remote_monitoring.syntrillo_database_manager import SyntrilloDatabaseManager
from syntrillo.api_tenovi.device_types import DeviceTypes
from syntrillo.api_tenovi.device_measurements import DeviceMeasurements
from syntrillo.pseudonyms_management.lookup_codes_management import LookUpCodesManagement

from syntrillo.clinical_decision_support.color_coding.blood_pressure_categories import ColorCodingBloodPressureCategories, ColorCodingBloodPressureCategoriesWrapper
from syntrillo.clinical_decision_support.color_coding.blood_pressure_rainbow import ColorCodingBloodPressureRainbows


class BloodPressureAnalysis:
    """
    Handle patient level blood pressure analysis, including:
        - Avg SBP/DBP
        - SBP/DBP standard deviation (SD)
        - SBP/DBP coefficent of variation (CV)
        - Peak SBP/DBP (avg of top 3)
        - Low SBP/DBP
        - Hyper/hypotensive counts
        - Progress Point calculation (per Tech Roadmap slide deck)
    """

    # class variables
    syntrillo_internal_key : uuid.UUID = None
    syntrillo_database_manager : SyntrilloDatabaseManager = None
    bpm_df : pd.DataFrame = None

    # color maps for systolic and diastolic
    alpha : float = 0.5

    # no data string
    no_data_string : str = "no data"


    def __init__(self, syntrillo_internal_key : uuid.UUID) -> None:

        self.syntrillo_internal_key = syntrillo_internal_key

        # set up PHI database connection for this user
        self.syntrillo_database_manager = SyntrilloDatabaseManager(syntrillo_internal_key)
