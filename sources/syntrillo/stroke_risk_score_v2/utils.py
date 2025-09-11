import math
import uuid
import pandas as pd
from syntrillo.system.logger import logger
from syntrillo.api_healthie.utils import HealthieUtils
from syntrillo.pseudonyms_management.lookup_codes_management import LookUpCodesManagement

def calculate_bmi(weight: float, height: float) -> float:
    """
    Calculate BMI from weight and height.
    Args:
        weight (float): The weight in pounds
        height (float): The height in inches
    Returns:
        float: The BMI
    """
    if weight is None or height is None:
        logger.warning(f"BMI is None for patient because weight or height was not provided...")
        return None
    # BMI = Weight (lb) / Height (in)² x 703
    bmi = weight / math.pow(height, 2) * 703
    return round(bmi, 2)

def get_biometric_data(syntrillo_internal_key: uuid.UUID) -> dict:
    """
    Get the biometric data for a given syntrillo internal key
    """
    try:
        logger.info(f"Getting biometric data for patient ...")
        lookup_codes = LookUpCodesManagement()
        healthie_utils = HealthieUtils()

        entry = lookup_codes.retrieve_entry_by_internal_key(syntrillo_internal_key=syntrillo_internal_key)
        healthie_user_id = entry['healthie_user_id']

        query="""
            query getUser($id: ID) {
                user(
                    id: $id
                    ) {
                    gender
                    height
                    weight
                    }
                }
        """
        variables = {
            "id": healthie_user_id,
        }

        # Retrieve the current set of responses
        response: dict= healthie_utils.run_graphql_query(query=query, variables=variables)
        data = response.get("user", None)
        logger.info(f"Successfully got biometric data for patient ...")

        height = data.get("height", None)
        weight = data.get("weight", None)
        if weight:
            weight = float(weight.split()[0])
        bmi = calculate_bmi(weight, height)


        return {
            "height": height,
            "weight": weight,
            "gender": data.get("gender", None),
            "bmi": bmi,
        }

    except Exception as e:
        logger.error(f"Error getting biometric data for syntrillo internal key {syntrillo_internal_key}: {e}")
        return None


def is_valid_timeframe(timeframe_df: pd.DataFrame, min_measurements: int = 3) -> bool:
    """Check if a timeframe has at least one valid (non-null) measurement and meets the min count."""
    return len(timeframe_df.dropna()) >= min_measurements and timeframe_df.notna().any().any()
