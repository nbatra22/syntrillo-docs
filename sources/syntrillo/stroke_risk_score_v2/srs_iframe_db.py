import uuid
from datetime import datetime
from typing import Optional, Tuple
from syntrillo.stroke_risk_score_v2.utils import calculate_bmi
from syntrillo.remote_monitoring.syntrillo_database_manager import SyntrilloDatabaseManager
from syntrillo.stroke_risk_score_v2.models.srs_form import SRSFormResponse

def get_srs_iframe_data(syntrillo_internal_key: uuid.UUID) -> Tuple[list[SRSFormResponse], dict]:
    """
    Given a patients syntrillo_internal_key, retireve all the srs form responses and compliance data

    Args:
        syntrillo_internal_key (uuid.UUID): The Syntrillo internal key

    Returns:
        srs_form_response (list[SRSFormResponse]): The SRS form responses
        log (dict): The log
    """

    # Given a patients syntrillo_internal_key, retireve all the srs form responses and compliance data
    db_manager = SyntrilloDatabaseManager(syntrillo_internal_key=syntrillo_internal_key)
    srs_form_response, log = db_manager.get_srs_all_responses(syntrillo_internal_key)

    return srs_form_response, log


def insert_srs_iframe_data(syntrillo_internal_key: uuid.UUID, data: dict) -> Tuple[Optional[int], dict]:
    """
    Insert SRS form responses and compliance data into the database

    Args:
        syntrillo_internal_key (uuid.UUID): The Syntrillo internal key
        data (dict): The data to insert

    Returns:
        srs_form_response_id (Optional[int]): The SRS form response ID
        log (dict): The log
    """

    db_manager = SyntrilloDatabaseManager(syntrillo_internal_key=syntrillo_internal_key)

    # Insert SRS form responses
    srs_form_response = SRSFormResponse(
        syntrillo_internal_key=syntrillo_internal_key,
        created_at=datetime.now(),
        **data
    )

    # Calculate BMI
    bmi = calculate_bmi(srs_form_response.Weight, srs_form_response.Height)
    srs_form_response.BMI = bmi

    # Insert SRS form response
    db_manager.insert_srs_form_response(srs_form_response)







if __name__ == "__main__":
    syntrillo_internal_key = uuid.UUID("125c56e8-5e93-4211-a287-f1fcfee11da3")
    srs_data = {
        "HasPreviousStroke": True,
        "ScreenedForTIA": True,
        "HasPriorHeadCT": True,
        "ChronicInfarctPresent": True,
        "HistoryOfAtrialFibrillation": True,
        "HistoryOfIronDeficiencyAnemia": True,
        "HistoryOfArterialClots": True,
        "HistoryOfVenousClots": True,
        "HistoryOfCHF": True,
        "HistoryOfCarotidStenosis": True,
        "HistoryOfOSA": True,
        "HistoryOfCAD": True,
        "HistoryOfValvularHeartDisease": True,
        "HistoryOfCKD": True,
    }
    insert_srs_iframe_data(syntrillo_internal_key, srs_data)