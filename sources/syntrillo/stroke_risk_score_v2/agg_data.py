from typing import Union
import uuid
from datetime import datetime

import pandas as pd

from syntrillo.system.logger import logger
from syntrillo.remote_monitoring.syntrillo_database_manager import SyntrilloDatabaseManager
from syntrillo.stroke_risk_score_v2.models.srs_form import SRSFormResponse
from syntrillo.bp_analysis.bp_analysis import BloodPressureAnalysis
from syntrillo.api_healthie.utils import HealthieUtils
from syntrillo.pseudonyms_management.lookup_codes_management import LookUpCodesManagement
from syntrillo.remote_monitoring.constants import PULSE_METRIC_NAME
from syntrillo.api_healthie.constants import RHR_CATEGORY, ENTRY_TYPE
from syntrillo.bp_analysis.constants import (
    TIMESTAMP_LOCAL,
    SYSTOLIC,
    DIASTOLIC,
    SBP_COUNT_175,
    AVG_SBP,
    SBP_SD,
    AVG_DBP,
    AVERAGE,
    VARIABILITY,
    TRAILING
)
from syntrillo.stroke_risk_score_v2.constants import (
    CREATED_AT,
    TYPE_BP,
    TYPE_RHR,
    TYPE_HR,
    TIMESTAMP,
    VALUE_1,
    INACTIVITY_INTAKE_MODULE_LABEL,
    INACTIVITY_CHARTING_MODULE_LABEL,
    ACTIVITY_INTAKE_MODULE_LABEL,
    ACTIVITY_CHARTING_MODULE_LABEL,
    BASELINE_NUM_WEEKS,
    TRAILING_NUM_WEEKS,
    TRAILING_NUM_DAYS,
    METRIC_STAT,
)


def aggregate_data(syntrillo_internal_key: uuid.UUID) -> dict:
    """
    Aggregate data from Tenovi, Healthie, and SRS response data

    Args:
        syntrillo_internal_key (uuid.UUID): The Syntrillo internal key

    Returns:
        dict: The aggregated data
        {
            "tenovi_bp_data": tenovi_bp_data,
            "healthie_srs_data": healthie_srs_data,
            "srs_response_data": srs_response_data,
            "lab_data": {},
            "substance_use_data": {},
        }
    """
    try:
        logger.info(f"Beginning to aggregate data for patient with syntrillo_internal_key {syntrillo_internal_key} ...")
        db_manager = SyntrilloDatabaseManager(syntrillo_internal_key)

        # Get healthie user id from lookup codes
        lookup_codes = LookUpCodesManagement()
        entry = lookup_codes.retrieve_entry_by_internal_key(syntrillo_internal_key=syntrillo_internal_key)
        healthie_user_id = entry['healthie_user_id']

        tenovi_bp_data = get_tenovi_bp_data(syntrillo_internal_key)
        healthie_srs_data = get_srs_healthie_data(healthie_user_id, db_manager)
        srs_response_data = get_srs_response_data(syntrillo_internal_key, db_manager)

        # NOT CURRENTLY USED BUT CAN BE USED IN FUTURE – tenovi_hr_data = get_tenovi_hr_data(db_manager)

        print(f"tenovi_bp_data: {tenovi_bp_data}")
        print(f"healthie_srs_data: {healthie_srs_data}")
        print(f"srs_response_data: {srs_response_data}")

        return {
            "tenovi_bp_data": tenovi_bp_data,
            "healthie_srs_data": healthie_srs_data,
            "srs_response_data": srs_response_data,
            "lab_data": {},
            "substance_use_data": {},
        }


    except Exception as e:
        logger.error(f"Error aggregating SRS data: {e}")
        raise ValueError("Error aggregating SRS data")

#########################################################
####### HEALTHIE DATA ###################################
#########################################################


# Get records using syntrillo_internal_key from srs_form_responses table
def get_srs_healthie_data(healthie_user_id: str, db_manager: SyntrilloDatabaseManager) -> dict:
    """
    Get the data needed for SRS calculations that is stored in healthie from the healthie user id
    Args:
        healthie_user_id (str): The healthie user id

    Returns:
        dict: The healthie data
        {
            "average_rhr_baseline": average_rhr_baseline,
            "average_rhr_trailing": average_rhr_trailing,
            "inactivity_hours_answer": inactivity_hours_answer,
            "activity_minutes_answer": activity_minutes_answer,
        }
    Raises:
        ValueError: If the healthie data is not valid
    """
    try:
        logger.info(f"Fetching RHR and Activity data from Healthie...")
        # Retreive resting hr from healthie
        healthie_utils = HealthieUtils()

        rhr_data = get_healthie_rhr_data(healthie_utils, healthie_user_id)
        rhr_metadata = calc_rhr_metadata(rhr_data) if rhr_data else None

        # Retreive the activity data
        activity_data = get_healthie_activity_data(healthie_user_id, db_manager)

        # None value will be used to indicate that there is no data to calculate the metadata
        # and this will impact the risk score calculation as no data means more attention is needed.
        logger.info(f"Successfully fetched RHR and Activity data from Healthie...")
        return {
            "average_rhr_baseline": rhr_metadata["average_rhr_baseline"] if rhr_metadata else None,
            "average_rhr_trailing": rhr_metadata["average_rhr_trailing"] if rhr_metadata else None,
            "inactivity_hours_answer": activity_data["inactivity_hours_answer"],
            "activity_minutes_answer": activity_data["activity_minutes_answer"],
        }

    except Exception as e:
        logger.error(f"Error fetching RHR data from healthie: {e}")
        raise ValueError("Error fetching RHR data from healthie")


def get_healthie_activity_data(healthie_user_id: str, db_manager: SyntrilloDatabaseManager) -> Union[int, None]:
    """
    Get the activity data from healthie
    Args:
        healthie_user_id (str): The healthie user id
        db_manager (SyntrilloDatabaseManager): The syntrillo database manager

    Returns:
        inactivity_minutes_answer (int | None): The patient's inactivity minutes form response answer
    Raises:
        ValueError: If the inactivity minutes answer is not valid
    """

    try:
        logger.info(f"Fetching activity data from healthie...")
        # Get the module ids for the intake and charting modules
        _, module_id_inactivity_intake = db_manager.get_form_module_ids_by_module_label(INACTIVITY_INTAKE_MODULE_LABEL)
        _, module_id_inactivity_charting = db_manager.get_form_module_ids_by_module_label(INACTIVITY_CHARTING_MODULE_LABEL)

        _, module_id_activity_intake = db_manager.get_form_module_ids_by_module_label(ACTIVITY_INTAKE_MODULE_LABEL)
        _, module_id_activity_charting = db_manager.get_form_module_ids_by_module_label(ACTIVITY_CHARTING_MODULE_LABEL)

        # Retreive the intake & charting inactivity value based on the module id and healthie user id
        intake_inactivity_hours_answer, intake_created_at = db_manager.get_patient_form_response_by_module_id(module_id_inactivity_intake, healthie_user_id)
        charting_inactivity_hours_answer, charting_created_at = db_manager.get_patient_form_response_by_module_id(module_id_inactivity_charting, healthie_user_id)

        intake_activity_minutes_answer, intake_activity_created_at = db_manager.get_patient_form_response_by_module_id(module_id_activity_intake, healthie_user_id)
        charting_activity_minutes_answer, charting_activity_created_at = db_manager.get_patient_form_response_by_module_id(module_id_activity_charting, healthie_user_id)

        # Use the most recent answer from the intake or charting responses
        if not intake_inactivity_hours_answer and not charting_inactivity_hours_answer:
            return {
                "inactivity_hours_answer": None,
                "activity_minutes_answer": None,
            }
        # TODO: use updated_at instead of created_at
        elif (not charting_inactivity_hours_answer) or intake_created_at > charting_created_at:
            inactivity_hours_answer = intake_inactivity_hours_answer
            activity_minutes_answer = intake_activity_minutes_answer
        else:
            inactivity_hours_answer = charting_inactivity_hours_answer
            activity_minutes_answer = charting_activity_minutes_answer

        # Convert to int for DB range comparison
        inactivity_hours_answer = int(inactivity_hours_answer)
        activity_minutes_answer = int(activity_minutes_answer)

        logger.info(f"Successfully fetched activity data from healthie...")
        return {
            "inactivity_hours_answer": inactivity_hours_answer,
            "activity_minutes_answer": activity_minutes_answer,
        }

    except Exception as e:
        logger.error(f"Error fetching activity data from healthie: {e}")
        raise ValueError("Error fetching activity data from healthie")


def get_healthie_rhr_data(healthie_utils: HealthieUtils, healthie_user_id: str, page_size: int = 100) -> dict:
    """
    Get the resting hr data from healthie using the syntrillo_internal_key

    Args:
        healthie_utils (HealthieUtils): The healthie utils
        healthie_user_id (str): The healthie user id

    Returns:
        dict: The resting hr data
    """
    logger.info(f"Fetching RHR data from healthie...")
    try:
        all_rhr_data = []
        cursor = None
        has_more_pages = True
        # Continue fetching pages until no more results
        while has_more_pages:
            query="""
                query entries(
                    $category: String
                    $client_id: String
                    $type: String
                    $page_size: Int
                    $after: Cursor
                    $sort_by: String
                ) {
                entries(
                    category: $category
                    client_id: $client_id
                    type: $type
                    page_size: $page_size
                    after: $after
                    sort_by: $sort_by
                ) {
                    category
                    created_at
                    metric_stat
                    metric_stat_string
                    source
                    third_party_source
                    cursor
                    }
                }
            """

            variables = {
                "client_id": healthie_user_id,
                "category": RHR_CATEGORY,
                "type": ENTRY_TYPE,
                "sort_by": "created_at::asc"
            }
            if cursor:
                variables["after"] = cursor

            # Retrieve the current set of responses
            response: dict= healthie_utils.run_graphql_query(query=query, variables=variables)
            current_page_data = response.get("entries", [])

            # Append the newest set of responses to output array
            all_rhr_data.extend(current_page_data)

            # Check if there are more pages to fetch
            if len(current_page_data) == page_size and current_page_data[-1].get("cursor"):
                cursor = current_page_data[-1]["cursor"]
                logger.info(f"Fetched {len(current_page_data)} records. Getting next page with cursor.")
            else:
                has_more_pages = False
                logger.info("No more pages to fetch.")

        logger.info(f"Successfully fetched {len(all_rhr_data)} RHR data points from healthie.")
        return all_rhr_data

    except Exception as e:
        logger.error(f"Error fetching RHR data from healthie: {e}")
        raise ValueError("Error fetching RHR data from healthie")



def calc_rhr_metadata(rhr_data: list[dict]) -> dict:
    """
    Calculate the RHR metadata from the rhr_data
    Args:
        rhr_data (list[dict]): The rhr data

    Returns:
        dict: The RHR metadata
    Raises:
        ValueError: If the RHR metadata is not valid
    """
    try:
        logger.info(f"Calculating RHR metadata...")
        # Convert rhr_data to pandas dataframe
        rhr_df = pd.DataFrame(rhr_data)

        # Clean the rhr_data
        rhr_df = rhr_df.drop(columns=['third_party_source', 'source', 'cursor', 'metric_stat_string', 'category'])
        rhr_df[CREATED_AT] = pd.to_datetime(rhr_df[CREATED_AT], errors='coerce') # ensure the created_at is a datetime

        # BASELINE DATAFRAME
        # Determine the baseline start and end dates
        baseline_start = rhr_df[CREATED_AT].min()
        baseline_end = baseline_start + pd.Timedelta(weeks=BASELINE_NUM_WEEKS)

        # Ensure the baseline dataframe is valid
        baseline_df = get_timeframed_data(rhr_df, baseline_start, baseline_end, TYPE_RHR)
        baseline_average = baseline_df[METRIC_STAT].mean() if not baseline_df.empty else None


        # TRAILING DATAFRAME
        # Determine the trailing start and end dates
        trailing_start = rhr_df[CREATED_AT].max() - pd.Timedelta(weeks=TRAILING_NUM_WEEKS)
        trailing_average = None
        if is_valid_trailing_timeframe_dates(trailing_start, baseline_end):
            trailing_end = rhr_df[CREATED_AT].max()
            trailing_df = get_timeframed_data(rhr_df, trailing_start, trailing_end, TYPE_RHR)

            # Calculate the average trailing for the rhr_data
            trailing_average = trailing_df[METRIC_STAT].mean() if not trailing_df.empty else None
        else:
            logger.error("Not enough data to calculate trailing average...")

        logger.info(f"Successfully calculated RHR metadata...")
        # Return the metadata
        return {
            "average_rhr_baseline": baseline_average,
            "average_rhr_trailing": trailing_average,
        }

    except Exception as e:
        logger.error(f"Error calculating RHR metadata: {e}")
        raise ValueError("Error calculating RHR metadata")







def get_srs_response_data(syntrillo_internal_key: uuid.UUID, db_manager: SyntrilloDatabaseManager) -> SRSFormResponse:
    """
    Get the most recent srs form response from the syntrillo_internal_key
    Args:
        syntrillo_internal_key (uuid.UUID): The syntrillo internal key
        db_manager (SyntrilloDatabaseManager): The syntrillo database manager

    Returns:
        SRSFormResponse: The most recent srs form response
    """
    try:
        srs_form_responses = db_manager.get_srs_form_responses(syntrillo_internal_key)
        # return most recent srs form response
        return srs_form_responses[0] if len(srs_form_responses) > 0 else None

    except Exception as e:
        logger.error(f"Error fetching SRS response data: {e}")
        raise ValueError("Error fetching SRS response data")

########################################################
####### TENOVI DATA ###################################
########################################################

def get_tenovi_hr_data(db_manager: SyntrilloDatabaseManager) -> dict:
    """
    Get the tenovi hr data (metric_name is pulse in DB). Only returns trailing variability for now.

    Args:
        db_manager (SyntrilloDatabaseManager): The syntrillo database manager
    Returns:
        dict: The trailing variability for the hr data
    Raises:
        ValueError: If the hr data is not valid
    """
    try:
        logger.info(f"Fetching Tenovi HR data...")
        hr_measurements, _ = db_manager.get_latest_measurements(metric_name=PULSE_METRIC_NAME)
        hr_df = pd.DataFrame(hr_measurements)

        # Convert timestamp to datetime
        hr_df[TIMESTAMP] = pd.to_datetime(hr_df[TIMESTAMP], errors='coerce')
        # Convert to numeric from string, value_1 is the hr data, value_2 is always 0
        hr_df[VALUE_1] = pd.to_numeric(hr_df[VALUE_1], errors='coerce')

        # Calculate variability for trailing 4 weeks HR data
        # Calculate the trailing start and end dates
        trailing_start = hr_df[TIMESTAMP].max() - pd.Timedelta(weeks=4)
        trailing_end = hr_df[TIMESTAMP].max()

        trailing_df = get_timeframed_data(hr_df, trailing_start, trailing_end, TYPE_HR)
        trailing_variability = trailing_df[VALUE_1].std() if not trailing_df.empty else None

        logger.info(f"Successfully fetched Tenovi HR data...")
        return trailing_variability

    except Exception as e:
        logger.error(f"Error getting Tenovi HR data: {e}")
        raise ValueError("Error getting Tenovi HR data")


# Get data from Tenovi
def get_tenovi_bp_data(syntrillo_internal_key: uuid.UUID) -> dict:
    """
    Get the tenovi bp data from the syntrillo_internal_key

    Args:
        syntrillo_internal_key (uuid.UUID): The syntrillo internal key

    Returns:
        dict: The tenovi bp data
        {
            SYSTOLIC: {
                TRAILING: {
                    PEAK: trailing_bp_metadata[PEAK_SBP],
                    VARIABILITY: trailing_bp_metadata[SBP_SD],
                    AVERAGE: trailing_bp_metadata[AVG_SBP],
                }
            },
            DIASTOLIC: {
                TRAILING: {
                    AVERAGE: trailing_bp_metadata[AVG_DBP],
                },
            },
        }
    Raises:
        ValueError: If the bp metadata is not valid
    """
    try:
        logger.info(f"Beginning Tenovi BP data aggregation...")
        bp_analysis = BloodPressureAnalysis(syntrillo_internal_key)
        bp_df, _ = bp_analysis.get_blood_pressure_dataframe()
        logger.info(f"Successfully fetched Tenovi BP data...")

        # Get baseline start date as it used in both baseline and trailing dataframes
        # Baseline start date is the first timestamp in the bp_df
        baseline_start = bp_df[TIMESTAMP_LOCAL].min()

        # Get the baseline and trailing dataframes
        logger.info(f"Getting baseline and trailing dataframes...")
        baseline_bp_df = get_baseline_bp_data(bp_df, baseline_start=baseline_start, baseline_weeks=BASELINE_NUM_WEEKS) # Get the baseline data
        trailing_bp_df = get_trailing_bp_data(bp_df, baseline_start=baseline_start, trailing_weeks=TRAILING_NUM_WEEKS, trailing_days=TRAILING_NUM_DAYS) # Get the trailing data

        # Calculate the bp metadata for the trailing and baseline dataframes
        bp_metadata = calc_bp_metadata(bp_analysis, trailing_bp_df, baseline_bp_df)

        return bp_metadata

    except Exception as e:
        logger.error(f"Error getting Tenovi BP data: {e}")
        raise ValueError("Error getting Tenovi BP data")



def get_baseline_bp_data(bp_dataframe: pd.DataFrame, baseline_start: datetime, baseline_weeks: int = 2) -> dict:
    """
    Get the baseline data (contains first 2 weeks of data) from the bp_dataframe
    Args:
        bp_dataframe (pd.DataFrame): The bp dataframe
        baseline_weeks (int): The number of baseline weeks. Default is 2.
        baseline_start (datetime): The start date of the baseline
    Returns:
        pd.DataFrame: The baseline data
    Raises:
        ValueError: If the baseline data is not valid
    """
    try:
        # Get the baseline start and end dates
        baseline_end = baseline_start + pd.Timedelta(weeks=baseline_weeks)

        # Get the baseline dataframe
        baseline_df = get_timeframed_data(bp_dataframe, baseline_start, baseline_end, TYPE_BP)
        return baseline_df if not baseline_df.empty else None

    except Exception as e:
        logger.error(f"Error getting baseline data: {e}")
        raise ValueError("Error getting baseline data")


def get_trailing_bp_data(bp_dataframe: pd.DataFrame, baseline_start: datetime, trailing_weeks: int = 4, trailing_days: int = 0) -> dict:
    """
    Get the trailing data (contains last 4 weeks of data and 0 days) from the bp_dataframe
    Args:
        bp_dataframe (pd.DataFrame): The bp dataframe
        baseline_start (datetime): The start date of the baseline
        trailing_weeks (int): The number of trailing weeks. Default is 4.
        trailing_days (int): The number of trailing days. Default is 0.

    Returns:
        pd.DataFrame: The trailing data
    Raises:
        ValueError: If the trailing data is not valid
    """
    try:
        # Get the trailing start and end dates
        trailing_end = bp_dataframe[TIMESTAMP_LOCAL].max()
        trailing_start = trailing_end - pd.Timedelta(weeks=trailing_weeks, days=trailing_days)

        if not is_valid_trailing_timeframe_dates(trailing_start, baseline_start):
            logger.error("Trailing data is not valid")
            raise ValueError("Trailing data is not valid")

        # Get the trailing dataframe
        trailing_df = get_timeframed_data(bp_dataframe, trailing_start, trailing_end, TYPE_BP)
        return trailing_df if not trailing_df.empty else None

    except Exception as e:
        logger.error(f"Error getting trailing data: {e}")
        raise ValueError("Error getting trailing data")


def calc_bp_metadata(bp_analysis: BloodPressureAnalysis, trailing_bp_dataframe: pd.DataFrame, baseline_bp_dataframe: pd.DataFrame) -> dict:
    """
    Calculate the bp metadata from the bp_dataframe
    Args:
        bp_analysis (BloodPressureAnalysis): The bp analysis object
        trailing_bp_dataframe (pd.DataFrame): The trailing bp dataframe
        baseline_bp_dataframe (pd.DataFrame): The baseline bp dataframe

    Returns:
        dict: The bp metadata
        {
            SYSTOLIC: {
                TRAILING: {
                    PEAK: trailing_bp_metadata[PEAK_SBP],
                    VARIABILITY: trailing_bp_metadata[SBP_SD],
                    AVERAGE: trailing_bp_metadata[AVG_SBP],
                },
            },
            DIASTOLIC: {
                TRAILING: {
                    AVERAGE: trailing_bp_metadata[AVG_DBP],
                },
            },
        }
    Raises:
        ValueError: If the bp metadata is not valid
    """
    try:
        logger.info(f"Calculating bp metadata...")
        # Calculate the metadata for the trailing dataframe
        trailing_bp_metadata = bp_analysis.calculate_metadata_v2(trailing_bp_dataframe)
        # NOT CURRENTLY USED BUT CAN BE USED IN FUTURE – baseline_bp_metadata = bp_analysis.calculate_metadata_v2(baseline_bp_dataframe)

        # Trim the metadata to only include the necessary data for SRS calculation
        trimmed_bp_metadata = {
            SYSTOLIC: {
                TRAILING: {
                    SBP_COUNT_175: trailing_bp_metadata[SBP_COUNT_175], # Considered the "PEAK" BP value for SRS
                    VARIABILITY: trailing_bp_metadata[SBP_SD],
                    AVERAGE: trailing_bp_metadata[AVG_SBP],
                }
            },
            DIASTOLIC: {
                TRAILING: {
                    AVERAGE: trailing_bp_metadata[AVG_DBP],
                },
            },
        }
        logger.info(f"Successfully calculated bp metadata...")
        return trimmed_bp_metadata

    except Exception as e:
        logger.error(f"Error calculating bp metadata: {e}")
        raise ValueError("Error calculating bp metadata")


def get_timeframed_data(dataframe: pd.DataFrame, timeframe_start: datetime, timeframe_end: datetime, type: str) -> pd.DataFrame:
    """
    Get the timeframed data from the dataframe
    Args:
        dataframe (pd.DataFrame): The dataframe
        timeframe_start (datetime): The start date of the timeframe
        timeframe_end (datetime): The end date of the timeframe

    Returns:
        pd.DataFrame: The timeframed data
    Raises:
        ValueError: If the timeframed data is not valid
    """
    try:
        if type == TYPE_BP:
            timeframe_df = dataframe[(dataframe[TIMESTAMP_LOCAL] >= timeframe_start) & (dataframe[TIMESTAMP_LOCAL] < timeframe_end)]
        elif type == TYPE_RHR:
            timeframe_df = dataframe[(dataframe[CREATED_AT] >= timeframe_start) & (dataframe[CREATED_AT] < timeframe_end)]
        elif type == TYPE_HR:
            timeframe_df = dataframe[(dataframe[TIMESTAMP] >= timeframe_start) & (dataframe[TIMESTAMP] < timeframe_end)]
        else:
            logger.error(f"Invalid type: {type}")
            raise ValueError(f"Invalid type: {type}")

        if not is_valid_timeframe_num_measurements(timeframe_df):
            logger.error("Timeframed data is not valid")
            return pd.DataFrame()

        return timeframe_df

    except Exception as e:
        logger.error(f"Error getting timeframed data: {e}")
        return pd.DataFrame()


def is_valid_timeframe_num_measurements(timeframe_df: pd.DataFrame, min_measurements: int = 3) -> bool:
    """
    Check if a timeframe has at least one valid (non-null) measurement and meets the min count.
    Args:
        timeframe_df (pd.DataFrame): The timeframe dataframe
        min_measurements (int): The minimum number of measurements. Default is 3.

    Returns:
        bool: True if the timeframe is valid, False otherwise
    """
    return len(timeframe_df.dropna()) >= min_measurements and timeframe_df.notna().any().any()

def is_valid_trailing_timeframe_dates(trailing_start: datetime, baseline_end: datetime) -> bool:
    """
    Check if the trailing timeframe is valid (trailing start is after baseline end)
    Args:
        trailing_start (datetime): The start date of the trailing timeframe
        baseline_end (datetime): The end date of the baseline timeframe

    Returns:
        bool: True if the trailing timeframe is valid, False otherwise
    """
    return trailing_start > baseline_end




if __name__ == "__main__":
    syntrillo_internal_key = uuid.UUID("ff8d04c4-9307-4171-888b-447047d5fa36")
    data = aggregate_data(syntrillo_internal_key)
    print(data)
