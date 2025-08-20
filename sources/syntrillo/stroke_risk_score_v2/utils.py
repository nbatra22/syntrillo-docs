import math
from datetime import datetime
from typing import Tuple
import uuid
import pandas as pd
from syntrillo.remote_monitoring.syntrillo_database_manager import SyntrilloDatabaseManager
from syntrillo.api_tenovi.device_measurements import DeviceMeasurements
from syntrillo.system.logger import logger

def calculate_bmi(weight, height):
    """
    Calculate BMI from weight and height.
    Args:
        weight (float): The weight in pounds
        height (float): The height in inches
    Returns:
        float: The BMI
    """
    if weight is None or height is None:
        return None
    # BMI = Weight (lb) / Height (in)² x 703
    bmi = weight / math.pow(height, 2) * 703
    return round(bmi, 2)



def is_valid_timeframe(timeframe_df: pd.DataFrame, min_measurements: int = 3) -> bool:
    """Check if a timeframe has at least one valid (non-null) measurement and meets the min count."""
    return len(timeframe_df.dropna()) >= min_measurements and timeframe_df.notna().any().any()
