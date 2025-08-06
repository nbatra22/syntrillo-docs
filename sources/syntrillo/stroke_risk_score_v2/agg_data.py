from typing import Tuple
import uuid
from datetime import datetime, timedelta

from syntrillo.remote_monitoring.syntrillo_database_manager import SyntrilloDatabaseManager
from syntrillo.api_tenovi.device_measurements import DeviceMeasurements
from syntrillo.stroke_risk_score_v2.models.srs_form import SRSFormResponse


def aggregate_data(syntrillo_internal_key: uuid.UUID) -> dict:
    """
    Aggregate data from Tenovi, Healthie, and SRS response data

    Args:
        syntrillo_internal_key (uuid.UUID): The Syntrillo internal key

    Returns:
        dict: The aggregated data
    """

    tenovi_data = get_tenovi_data(syntrillo_internal_key)
    healthie_srs_data = get_srs_healthie_data(syntrillo_internal_key)
    srs_response_data = get_srs_response_data(syntrillo_internal_key)

    return {
        "tenovi_data": tenovi_data,
        "healthie_srs_data": healthie_srs_data,
        "srs_response_data": srs_response_data,
    }


# Get data from Tenovi
def get_tenovi_data(syntrillo_internal_key: uuid.UUID):
    db_manager = SyntrilloDatabaseManager(syntrillo_internal_key)

    # -- What is the time range for the data for Variability, Peak, Average, Baseline?
    # HR - Variability, Resting
    # Resting HR - Baseline
    # Systolic BP - Peak, Variability, Average, Baseline
    # Diastolic BP - Baseline, Average

    df, log = db_manager.get_tenovi_device_metric_data(
        metric_name=DeviceMeasurements.TENOVI_METRICS_BPM_BLOOD_PRESSURE,
        start_date=datetime.now() - timedelta(days=30),
        end_date=datetime.now()
    )

    return df, log

# Get records using syntrillo_internal_key from srs_form_responses table
def get_srs_healthie_data(syntrillo_internal_key: uuid.UUID) -> Tuple[list[SRSFormResponse], dict]:
    pass

def get_srs_response_data(syntrillo_internal_key: uuid.UUID) -> Tuple[list[SRSFormResponse], dict]:
    db_manager = SyntrilloDatabaseManager(syntrillo_internal_key)
    srs_form_responses, _ = db_manager.get_srs_form_responses(syntrillo_internal_key)

    # return most recent srs form response
    return srs_form_responses[0]


if __name__ == "__main__":
    syntrillo_internal_key = uuid.UUID("125c56e8-5e93-4211-a287-f1fcfee11da3")
    data = aggregate_data(syntrillo_internal_key)
    print(data)