import uuid
from datetime import datetime
from typing import Optional, Tuple
from syntrillo.stroke_risk_score_v2.utils import calculate_bmi
from syntrillo.remote_monitoring.syntrillo_database_manager import SyntrilloDatabaseManager
from syntrillo.stroke_risk_score_v2.models.srs_form import (
    SRSFormResponse,
    NumberOfStrokesOptions,
    StrokeMechanismOptions,
    LikelihoodOfTIAOptions,
    AnemiaSeverityOptions,
    ArterialClotOccurrencesOptions,
    PFOPresenceOptions,
    VenousClotOccurrencesOptions,
    EjectionFractionOptions,
    StenosisPercentageOptions,
    OSASeverityOptions,
    CADTypeOptions,
    PhysicalInactivityLevelOptions,
    LDLLevelOptions,
    HDLLevelOptions,
    TriglyceridesLevelOptions,
    )
from syntrillo.stroke_risk_score_v2.models.treatment_compliance import TreatmentCompliance, TreatmentComplianceOptions
from syntrillo.system.logger import logger


def get_srs_iframe_data(syntrillo_internal_key_patient: uuid.UUID) -> Tuple[list[SRSFormResponse], dict]:
    """
    Given a patients syntrillo_internal_key, retireve all the srs form responses and compliance data

    Args:
        syntrillo_internal_key (uuid.UUID): The Syntrillo internal key

    Returns:
        srs_form_response (list[SRSFormResponse]): The SRS form responses
        log (dict): The log
    """

    # Given a patients syntrillo_internal_key, retireve all the srs form responses and compliance data
    db_manager = SyntrilloDatabaseManager(syntrillo_internal_key=syntrillo_internal_key_patient)
    srs_form_responses, log = db_manager.get_srs_form_responses(syntrillo_internal_key_patient)

    return srs_form_responses, log


def insert_srs_iframe_data(syntrillo_internal_key_patient: uuid.UUID, syntrillo_internal_key_clinician: uuid.UUID, data: dict) -> Tuple[Optional[int], dict]:
    """
    Insert SRS form responses and compliance data into the database

    Args:
        syntrillo_internal_key_patient (uuid.UUID): The Syntrillo internal key of the patient who the SRS form is for
        syntrillo_internal_key_clinician (uuid.UUID): The Syntrillo internal key of the clinician who created the SRS form is for
        data (dict): The data to insert

    Returns:
        srs_form_response_id (Optional[int]): The SRS form response ID
        log (dict): The log
    """
    try:
        logger.info(f"Inserting SRS form response for patient {syntrillo_internal_key_patient} and clinician {syntrillo_internal_key_clinician}...")
        db_manager = SyntrilloDatabaseManager(syntrillo_internal_key=syntrillo_internal_key_patient)

        # Insert SRS form responses
        srs_form_response = SRSFormResponse(
            syntrillo_internal_key_patient=str(syntrillo_internal_key_patient),
            syntrillo_internal_key_clinician=str(syntrillo_internal_key_clinician),
            created_at=datetime.now(),
            **data
        )

        # Calculate BMI
        bmi = calculate_bmi(srs_form_response.Weight, srs_form_response.Height)
        if bmi is None:
            logger.warning(f"BMI is None for patient {syntrillo_internal_key_patient} because weight or height was not provided...")
        srs_form_response.BMI = bmi

        # Insert SRS form response
        srs_form_response_id, log = db_manager.insert_srs_form_response(srs_form_response)

        logger.info(f"Successfully inserted SRS form response for patient {syntrillo_internal_key_patient} with ID: {srs_form_response_id}")
        return srs_form_response_id, log

    except Exception as e:
        logger.error(f"Error inserting SRS form response for patient {syntrillo_internal_key_patient}: {e}")
        return None, {"success": False, "error": str(e)}








if __name__ == "__main__":

    # syntrillo_internal_key_patient = uuid.UUID("6446f4da-b19a-4a1a-851e-06b5bc716160")
    # srs_form_responses, log = get_srs_iframe_data(syntrillo_internal_key_patient)
    # print(srs_form_responses)

    # syntrillo_internal_key_patient = uuid.UUID("ff8d04c4-9307-4171-888b-447047d5fa36")
    # syntrillo_internal_key_clinician = uuid.UUID("77f96276-c864-43b7-8baa-567b033472fc")
    # srs_data = {
    #     "HasPreviousStroke": True,
    #     "ScreenedForTIA": True,
    #     "HasPriorHeadCT": True,
    #     "ChronicInfarctPresent": True,
    #     "HistoryOfAtrialFibrillation": True,
    #     "HistoryOfIronDeficiencyAnemia": True,
    #     "HistoryOfArterialClots": True,
    #     "HistoryOfVenousClots": True,
    #     "HistoryOfCHF": True,
    #     "HistoryOfCarotidStenosis": True,
    #     "HistoryOfOSA": True,
    #     "HistoryOfCAD": True,
    #     "HistoryOfValvularHeartDisease": True,
    #     "HistoryOfCKD": True,
    #     "NumberOfStrokes": NumberOfStrokesOptions.MULTIPLE,
    #     "LatestStrokeMechanism": StrokeMechanismOptions.LARGE_VESSEL,
    #     "LikelihoodOfTIA": LikelihoodOfTIAOptions.HIGH_LIKELIHOOD,
    #     "TIAMechanism": StrokeMechanismOptions.LARGE_VESSEL,
    #     "ChronicInfarctMechanism": StrokeMechanismOptions.LARGE_VESSEL,
    #     "AnemiaSeverity": AnemiaSeverityOptions.MILD,
    #     "ArterialClotOccurrences": ArterialClotOccurrencesOptions.SINGLE_PRIOR_EVENT,
    #     "PFOPresence": PFOPresenceOptions.POSITIVE,
    #     "VenousClotOccurrences": VenousClotOccurrencesOptions.SINGLE,
    #     "EjectionFraction": EjectionFractionOptions.LESS_THAN_OR_EQUAL_40,
    #     "StenosisPercentage": StenosisPercentageOptions.FIFTY_TO_SEVENTY,
    #     "OSASeverity": OSASeverityOptions.MILD,
    #     "CADType": CADTypeOptions.SYMPTOMATIC_MULTI_OR_SINGLE_VESSEL,
    #     "Gender": GenderOptions.MAN,
    #     "Creatinine": 1.0,
    #     "AvgSBP": 120,
    #     "RHR": 60,
    #     "Height": 71.0,
    #     "Weight": 175.5,
    #     "HemoglobinA1c": 5.0,
    #     "PhysicalInactivityHours": 10.0,
    #     "PhysicalActivityMinutes": 10.0,
    #     "Triglycerides": 100.0,
    #     "LDL": 99.0,
    #     "HDL": 30.0,
    #     "PriorCTDate": datetime.now(),
    #     "compliance": TreatmentCompliance(
    #         strokeCompliance=TreatmentComplianceOptions.OPTIMIZED,
    #         tiaCompliance=TreatmentComplianceOptions.OPTIMIZED,
    #         chronicInfarctCompliance=TreatmentComplianceOptions.OPTIMIZED,
    #         atrialFibrillationCompliance=TreatmentComplianceOptions.OPTIMIZED,
    #         arterialClotsCompliance=TreatmentComplianceOptions.OPTIMIZED,
    #         venousClotsCompliance=TreatmentComplianceOptions.OPTIMIZED,
    #         chfCompliance=TreatmentComplianceOptions.OPTIMIZED,
    #         carotidStenosisCompliance=TreatmentComplianceOptions.OPTIMIZED,
    #         osaCompliance=TreatmentComplianceOptions.OPTIMIZED,
    #         cadCompliance=TreatmentComplianceOptions.OPTIMIZED,
    #         ironDeficiencyAnemiaCompliance=TreatmentComplianceOptions.OPTIMIZED,
    #         valvularHeartDiseaseCompliance=TreatmentComplianceOptions.OPTIMIZED,
    #         ckdCompliance=TreatmentComplianceOptions.OPTIMIZED,
    #         triglyceridesCompliance=TreatmentComplianceOptions.OPTIMIZED,
    #         ldlCompliance=TreatmentComplianceOptions.OPTIMIZED,
    #         hdlCompliance=TreatmentComplianceOptions.OPTIMIZED,
    #     )
    # }
    # insert_srs_iframe_data(syntrillo_internal_key_patient, syntrillo_internal_key_clinician, srs_data)


    # Staging Test Patient (modeled from Omar's Prod data)
    # syntrillo_internal_key_patient = uuid.UUID("ff8d04c4-9307-4171-888b-447047d5fa36")
    # syntrillo_internal_key_clinician = uuid.UUID("77f96276-c864-43b7-8baa-567b033472fc")

    # srs_data = {
    #     "HasPreviousStroke": True,
    #     "NumberOfStrokes": NumberOfStrokesOptions.ONE,
    #     "LatestStrokeMechanism": StrokeMechanismOptions.CARDIOEMBOLIC,
    #     "Gender": GenderOptions.WOMAN,
    #     "HistoryOfAtrialFibrillation": True,
    #     "LDL": 140.0,
    #     "HDL": 45.0,
    #     "Height": 72.0,
    #     "Weight": 255.0,
    #     "compliance": TreatmentCompliance(
    #         strokeCompliance=TreatmentComplianceOptions.OPTIMIZED,
    #         atrialFibrillationCompliance=TreatmentComplianceOptions.OPTIMIZED,
    #         ldlCompliance=TreatmentComplianceOptions.OPTIMIZED,
    #         hdlCompliance=TreatmentComplianceOptions.OPTIMIZED,
    #         triglyceridesCompliance=TreatmentComplianceOptions.OPTIMIZED,
    #     )
    # }

    syntrillo_internal_key_patient = uuid.UUID("99fddf03-9304-4e48-8711-0cc4d825eb94")
    syntrillo_internal_key_clinician = uuid.UUID("77f96276-c864-43b7-8baa-567b033472fc")

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
        "NumberOfStrokes": NumberOfStrokesOptions.MULTIPLE,
        "LatestStrokeMechanism": StrokeMechanismOptions.LARGE_VESSEL,
        "LikelihoodOfTIA": LikelihoodOfTIAOptions.HIGH_LIKELIHOOD,
        "TIAMechanism": StrokeMechanismOptions.LARGE_VESSEL,
        "ChronicInfarctMechanism": StrokeMechanismOptions.LARGE_VESSEL,
        "AnemiaSeverity": AnemiaSeverityOptions.MILD,
        "ArterialClotOccurrences": ArterialClotOccurrencesOptions.SINGLE_PRIOR_EVENT,
        "PFOPresence": PFOPresenceOptions.POSITIVE,
        "VenousClotOccurrences": VenousClotOccurrencesOptions.SINGLE,
        "EjectionFraction": EjectionFractionOptions.LESS_THAN_OR_EQUAL_40,
        "StenosisPercentage": StenosisPercentageOptions.FIFTY_TO_SEVENTY,
        "OSASeverity": OSASeverityOptions.MILD,
        "CADType": CADTypeOptions.SYMPTOMATIC_MULTI_OR_SINGLE_VESSEL,
        "PhysicalInactivityLevel": PhysicalInactivityLevelOptions.MILD,
        "LDLLevel": LDLLevelOptions.BORDERLINE,
        "HDLLevel": HDLLevelOptions.LOW,
        "TriglyceridesLevel": TriglyceridesLevelOptions.MODERATE,
        "CreatineLevel": 1.0,
        "AvgSBP": 120,
        "RHR": 60,
        "Height": 71.0,
        "Weight": 175.5,
        "HemoglobinA1c": 5.0,
        "compliance": TreatmentCompliance(
            strokeCompliance=TreatmentComplianceOptions.OPTIMIZED,
            tiaCompliance=TreatmentComplianceOptions.OPTIMIZED,
            chronicInfarctCompliance=TreatmentComplianceOptions.OPTIMIZED,
            atrialFibrillationCompliance=TreatmentComplianceOptions.OPTIMIZED,
            ironDeficiencyAnemiaCompliance=TreatmentComplianceOptions.OPTIMIZED,
            arterialClotsCompliance=TreatmentComplianceOptions.OPTIMIZED,
            venousClotsCompliance=TreatmentComplianceOptions.OPTIMIZED,
            chfCompliance=TreatmentComplianceOptions.OPTIMIZED,
            carotidStenosisCompliance=TreatmentComplianceOptions.OPTIMIZED,
            osaCompliance=TreatmentComplianceOptions.OPTIMIZED,
            cadCompliance=TreatmentComplianceOptions.OPTIMIZED,
            valvularHeartDiseaseCompliance=TreatmentComplianceOptions.OPTIMIZED,
            ckdCompliance=TreatmentComplianceOptions.OPTIMIZED,
            pfoCompliance=TreatmentComplianceOptions.OPTIMIZED,
        )
    }

    # insert_srs_iframe_data(syntrillo_internal_key_patient, syntrillo_internal_key_clinician, srs_data)
    srs_form_responses, log = get_srs_iframe_data(syntrillo_internal_key_patient)
    print(srs_form_responses)