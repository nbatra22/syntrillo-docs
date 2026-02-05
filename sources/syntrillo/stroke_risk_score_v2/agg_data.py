import json
from typing import Union
import uuid
from datetime import datetime
from typing import List
import pandas as pd
from syntrillo.system.logger import logger
from syntrillo.remote_monitoring.syntrillo_database_manager import SyntrilloDatabaseManager
from syntrillo.system.local_environment_and_secrets import LocalEnvironmentAndSecrets
from syntrillo.pseudonyms_management.lookup_codes_management import LookUpCodesManagement
from syntrillo.stroke_risk_score_v2.utils import get_biometric_data, fetch_all_form_responses_from_healthie
from syntrillo.api_healthie.utils import HealthieUtils
from syntrillo.stroke_risk_score_v2.models.srs_form import (
    SRSFormResponse,
    GenderOptions,
    VenousClotOccurrencesOptions,
    EjectionFractionOptions,
    PFOPresenceOptions,
    CADTypeOptions,
    StenosisPercentageOptions,
    OSASeverityOptions,
    ArterialClotOccurrencesOptions
)
from syntrillo.stroke_risk_score_v2.models.lab_data import LabData
from syntrillo.bp_analysis.bp_analysis import BloodPressureAnalysis
from syntrillo.remote_monitoring.constants import PULSE_METRIC_NAME
from syntrillo.api_healthie.constants import (
    RHR_CATEGORY,
    ENTRY_TYPE,
    LDL_CATEGORY,
    HDL_CATEGORY,
    HGA1C_CATEGORY,
    HSCRP_CATEGORY,
    HEMOGLOBIN_CATEGORY,
    CREATINTINE_CATEGORY,
    HOURS_SITTING_CATEGORY,
    PHYSICAL_ACTIVITY_MINS_CATEGORY,
    SSQ_CATEGORY,
)
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
    TRAILING,
    PEAK_AVG_SBP,
    PEAK_SBP,
    BASELINE
)
from syntrillo.stroke_risk_score_v2.constants import (
    CREATED_AT,
    TYPE_BP,
    TYPE_RHR,
    TYPE_HR,
    TYPE_PULSE,
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

GENDER_MAPPING = {
    "male": GenderOptions.MAN,
    "female": GenderOptions.WOMAN,
}


def aggregate_data(syntrillo_internal_key: uuid.UUID, is_ondemand_srs: bool = False, gender: GenderOptions = GenderOptions.MAN) -> dict:
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
            "lab_data": lab_data,
            "substance_use_data": {},
        }
    """
    try:
        logger.info(f"Beginning to aggregate data for patient with syntrillo_internal_key {syntrillo_internal_key} ...")
        db_manager = SyntrilloDatabaseManager(syntrillo_internal_key)
        healthie_utils = HealthieUtils()

        # Get healthie user id from lookup codes
        lookup_codes = LookUpCodesManagement()
        entry = lookup_codes.retrieve_entry_by_internal_key(syntrillo_internal_key=syntrillo_internal_key)

        if not entry:
            return {}
        healthie_user_id = entry['healthie_user_id']

        tenovi_bp_data = get_tenovi_bp_data(syntrillo_internal_key)
        tenovi_hr_data = get_tenovi_hr_data(db_manager)
        healthie_srs_data = get_srs_healthie_data(healthie_user_id, db_manager, syntrillo_internal_key, healthie_utils)
        lab_data = get_lab_data(healthie_utils=healthie_utils, healthie_user_id=healthie_user_id)

        if is_ondemand_srs:
            patient_history_data = get_patient_history_data(healthie_user_id=healthie_user_id)
            srs_response_data = [
                SRSFormResponse(
                    syntrillo_internal_key_patient= str(syntrillo_internal_key),
                    created_at=datetime.now(),
                    Gender=gender,
                )
            ]
            srs_response_data[0] = populate_with_patient_history(srs_response_data[0], patient_history_data, syntrillo_internal_key)
        else:
            srs_response_data = get_srs_response_data(syntrillo_internal_key, db_manager)

        return {
            "tenovi_bp_data": tenovi_bp_data,
            "tenovi_hr_data": tenovi_hr_data,
            "healthie_srs_data": healthie_srs_data,
            "srs_response_data": srs_response_data,
            "lab_data": lab_data,
            "substance_use_data": {},
        }

    except Exception as e:
        logger.error(f"Error aggregating SRS data: {e}")
        raise ValueError("Error aggregating SRS data")

def populate_with_patient_history(srs_response_data: SRSFormResponse, patient_history_data: dict, syntrillo_internal_key):

    srs_response_data.HasPreviousStroke = patient_history_data["hasPriorStroke"]
    srs_response_data.NumberOfStrokes = patient_history_data["numOfPriorStrokes"]
    srs_response_data.HasPriorHeadCT = patient_history_data["priorHeadCT"]
    srs_response_data.ChronicInfarctPresent = patient_history_data["hasChronicInfarct"]
    srs_response_data.HistoryOfAtrialFibrillation = patient_history_data["atrialFibrillationHasHistory"]
    srs_response_data.HistoryOfIronDeficiencyAnemia = patient_history_data["ironDeficiencyAnemiaHasHistory"]
    srs_response_data.HistoryOfArterialClots = patient_history_data["arterialClotsHasHistory"]
    srs_response_data.ArterialClotOccurrences = patient_history_data["arterialClotsNumberOfOccurances"]
    srs_response_data.HistoryOfVenousClots = patient_history_data["venousClotsHasHistory"]
    srs_response_data.VenousClotOccurrences = patient_history_data["venousClotsNumberOfOccurances"]
    srs_response_data.PFOPresence = patient_history_data["venousClotsPfoHasHistory"]
    srs_response_data.HistoryOfCHF = patient_history_data["chfHasHistory"]
    srs_response_data.EjectionFraction = patient_history_data["chfEf"]
    srs_response_data.HistoryOfCarotidStenosis = patient_history_data["carotidStenosisHasHistory"]
    srs_response_data.StenosisPercentage = patient_history_data["carotidStenosisDegree"]
    srs_response_data.HistoryOfOSA = patient_history_data["osaHasHistory"]
    srs_response_data.OSASeverity = patient_history_data["osaSeverity"]
    srs_response_data.HistoryOfCAD = patient_history_data["cadHasHistory"]
    srs_response_data.CADType = patient_history_data["cadType"]
    srs_response_data.HistoryOfValvularHeartDisease = patient_history_data["valvularHeartDiseaseHasHistory"]
    srs_response_data.HistoryOfCKD = patient_history_data["ckdHasHistory"]

    # Get patient specific biometric data from Healthie
    biometric_data = get_biometric_data(syntrillo_internal_key)
    # Update SRSFormResponse object with new data
    srs_response_data.Height = biometric_data.get("height", None)
    srs_response_data.Gender = GENDER_MAPPING[biometric_data["gender"].lower() if biometric_data["gender"] else "male"]
    srs_response_data.Weight = biometric_data.get("weight", None)
    srs_response_data.BMI = biometric_data.get("bmi", None)

    return srs_response_data




# def initial_srs_calc(syntrillo_internal_key: uuid.UUID):
#     logger.info(f"Beginning to aggregate data for patient with syntrillo_internal_key {syntrillo_internal_key} ...")
#     db_manager = SyntrilloDatabaseManager(syntrillo_internal_key)
#     healthie_utils = HealthieUtils()

#     # Get healthie user id from lookup codes
#     lookup_codes = LookUpCodesManagement()
#     entry = lookup_codes.retrieve_entry_by_internal_key(syntrillo_internal_key=syntrillo_internal_key)

#     if not entry:
#         return {}
#     healthie_user_id = entry['healthie_user_id']

#     tenovi_bp_data = get_tenovi_bp_data(syntrillo_internal_key)
#     tenovi_hr_data = get_tenovi_hr_data(db_manager)
#     healthie_srs_data = get_srs_healthie_data(healthie_user_id, db_manager, syntrillo_internal_key, healthie_utils)
#     lab_data = get_lab_data(healthie_utils=healthie_utils, healthie_user_id=healthie_user_id)
#     patient_history_data = get_patient_history_data(healthie_user_id=healthie_user_id)



#########################################################
####### HEALTHIE DATA ###################################
#########################################################

def get_patient_history_data(healthie_user_id: str):
    """
    """
    # Fetch the patient's responses to the Healthie form "Onboarding Record Review w/ Patient [v9.2]"" (as of 11/12/25).

    # Map Healthie form inputs to result object
    secrets = LocalEnvironmentAndSecrets(load_healthie_ids_secrets=True)
    form_id = secrets.get_secret_value('healthie_ids', 'srs_charting_note_id')

    # tolerant parsing: secret may be a dict (plaintext object), a JSON string, or bytes
    raw_qids = secrets.get_secret_value('healthie_ids', 'srs_charting_note_question_ids')
    if isinstance(raw_qids, dict):
        srs_attribute_to_question_id = raw_qids
    else:
        if raw_qids is None:
            srs_attribute_to_question_id = {}
        else:
            # decode bytes, strip accidental outer quotes, then try json.loads
            try:
                if isinstance(raw_qids, (bytes, bytearray)):
                    raw_qids = raw_qids.decode()
                srs_attribute_to_question_id = json.loads(raw_qids)
            except Exception:
                try:
                    srs_attribute_to_question_id = json.loads(str(raw_qids).strip('\'"'))
                except Exception:
                    logger.warning("Could not parse srs_charting_note_question_ids secret; defaulting to empty dict")
                    srs_attribute_to_question_id = {}

    payload = fetch_all_form_responses_from_healthie(form_id=form_id)

    all_form_groups = payload.get('formAnswerGroups', [])

    # Initialize patient history dictionary with None values
    patient_history = {
        "hasPriorStroke": None,
        "numOfPriorStrokes": None,
        "priorHeadCT": None,
        "hasChronicInfarct": None,
        "atrialFibrillationHasHistory": None,
        "ironDeficiencyAnemiaHasHistory": None,
        "arterialClotsHasHistory": None,
        "arterialClotsNumberOfOccurances": None,
        "venousClotsHasHistory": None,
        "venousClotsNumberOfOccurances": None,
        "venousClotsPfoHasHistory": None,
        "chfHasHistory": None,
        "chfEf": None,
        "carotidStenosisHasHistory": None,
        "carotidStenosisDegree": None,
        "osaHasHistory": None,
        "osaSeverity": None,
        "cadHasHistory": None,
        "cadType": None,
        "valvularHeartDiseaseHasHistory": None,
        "ckdHasHistory": None
    }

    if not all_form_groups:
        return patient_history

    # 1. Filter for patient-specific form groups
    patient_form_groups = []
    for answer_group in all_form_groups:
        # Check 'form_answers' exists and is not empty
        if answer_group.get('form_answers'):
            # Check the user_id of the first answer – assumeing all answers in a group have same user_id
            first_answer = answer_group['form_answers'][0]
            if first_answer.get('user_id') == healthie_user_id:
                patient_form_groups.append(answer_group)

    # If no forms were found for this patient, return an empty list
    if not patient_form_groups:
        return patient_history

    # 2. Filter for the most recent form response
    try:
        # Find the group with the maximum (latest) 'created_at' timestamp.
        most_recent_group = max(
            patient_form_groups,
            key=lambda g: datetime.strptime(g['created_at'], '%Y-%m-%d %H:%M:%S %z')
        )
    except ValueError as e:
        # Handle cases where the date format might be wrong
        print(f"Error parsing date: {e}")
        return patient_history  # Return empty on error


    most_recent_answers = most_recent_group.get('form_answers', [])

    for answer in most_recent_answers:
        question_id = answer.get("custom_module", {}).get("id")

        patient_answer = answer.get("displayed_answer")
        if not patient_answer or "null" in patient_answer:
            continue

        # Has prior stroke – parse "Yes\nNo"
        if question_id == srs_attribute_to_question_id.get('hasPriorStroke'):
            patient_history["hasPriorStroke"] = True if patient_answer == "Yes" else False

        # Num of prior strokes – parse int
        elif question_id == srs_attribute_to_question_id.get('numOfPriorStrokes'):
            patient_history["numOfPriorStrokes"] = int(patient_answer)

        # Has prior Head CT – parse "Yes\nNo\nUnsure"
        elif question_id == srs_attribute_to_question_id.get('priorHeadCT'):
            patient_history["priorHeadCT"] = True if patient_answer == "Yes" else False

        # Has Chronic Infarct – parse "Yes\nNo\nUnsure"
        elif question_id == srs_attribute_to_question_id.get('hasChronicInfarct'):
            patient_history["hasChronicInfarct"] = True if patient_answer == "Yes" else False

        # Get histories
        elif question_id == srs_attribute_to_question_id.get('histories'):
            patient_history["atrialFibrillationHasHistory"] = True if "Atrial Fibrillation" in patient_answer else False
            patient_history["ironDeficiencyAnemiaHasHistory"] = True if "Iron" in patient_answer else False
            patient_history["arterialClotsHasHistory"] = True if "Arterial Clots" in patient_answer else False
            patient_history["venousClotsHasHistory"] = True if "Venous Clots" in patient_answer else False
            patient_history["chfHasHistory"] = True if "CHF" in patient_answer else False
            patient_history["carotidStenosisHasHistory"] = True if "Carotid Stenosis" in patient_answer else False
            patient_history["osaHasHistory"] = True if "Obstructive Sleep Apnea" in patient_answer else False
            patient_history["cadHasHistory"] = True if "CAD" in patient_answer else False
            patient_history["valvularHeartDiseaseHasHistory"] = True if "Valvular Heart Disease" in patient_answer else False
            patient_history["ckdHasHistory"] = True if "CKD" in patient_answer else False

        # CAD type # parse "Symptomatic\nAsymptomatic single vessel \nAsymptomatic multivessel\nUnknown"
        elif question_id == srs_attribute_to_question_id.get('cadType'):
            if "Symptomatic" in patient_answer:
                patient_history["cadType"] = CADTypeOptions.SYMPTOMATIC_MULTI_OR_SINGLE_VESSEL
            elif "Asymptomatic" in patient_answer:
                if "multivessel" in patient_answer:
                    patient_history["cadType"] = CADTypeOptions.ASYMPTOMATIC_MULTIVESSEL
                else:
                    patient_history["cadType"] = CADTypeOptions.ASYMPTOMATIC_SINGLE_VESSEL
            else:
                patient_history["cadType"] = CADTypeOptions.UNKNOWN

        # EF levels # parse "EF <= 40%\nEF > 40%\nEF Unkown"
        elif question_id == srs_attribute_to_question_id.get('chfEf'):
            if "<=" in patient_answer:
                patient_history["chfEf"] = EjectionFractionOptions.LESS_THAN_OR_EQUAL_40
            elif ">" in patient_answer:
                patient_history["chfEf"] = EjectionFractionOptions.GREATER_THAN_40
            else:
                patient_history["chfEf"] = EjectionFractionOptions.UNKNOWN

        # Carotid Stenosis # parse – "50-70% stenosis\n> 70% stenosis\nUnknown"
        elif question_id == srs_attribute_to_question_id.get('carotidStenosisDegree'):
            if "50" in patient_answer:
                patient_history["carotidStenosisDegree"] = StenosisPercentageOptions.FIFTY_TO_SEVENTY
            elif "70" in patient_answer:
                patient_history["carotidStenosisDegree"] = StenosisPercentageOptions.GREATER_THAN_SEVENTY
            else:
                patient_history["carotidStenosisDegree"] = StenosisPercentageOptions.UNKNOWN

        # OSA # parse – "Mild\nModerate\nSevere\nUnkown"
        elif question_id == srs_attribute_to_question_id.get('osaSeverity'):
            if "Mild" in patient_answer:
                patient_history["osaSeverity"] = OSASeverityOptions.MILD
            elif "Moderate" in patient_answer:
                patient_history["osaSeverity"] = OSASeverityOptions.MODERATE
            elif "Severe" in patient_answer:
                patient_history["osaSeverity"] = OSASeverityOptions.SEVERE
            else:
                patient_history["osaSeverity"] = OSASeverityOptions.UNKNOWN

        # Arterial Clots – parse "Single prior event \nMultiple prior events\nUnkown"
        elif question_id == srs_attribute_to_question_id.get('arterialClotsNumberOfOccurances'):
            if "Single" in patient_answer:
                patient_history["arterialClotsNumberOfOccurances"] = ArterialClotOccurrencesOptions.SINGLE_PRIOR_EVENT
            elif "Multiple" in patient_answer:
                patient_history["arterialClotsNumberOfOccurances"] = ArterialClotOccurrencesOptions.MULTIPLE_PRIOR_EVENTS

        # Venous Clots – parse "Single event\nMultiple events\nPFO treated\nPFO untreated \nUnknown"
        elif question_id == srs_attribute_to_question_id.get('venousClotsNumberOfOccurances'):
            first_word = patient_answer.strip().split()[0]

            if first_word == "Single":
                patient_history["venousClotsNumberOfOccurances"] = VenousClotOccurrencesOptions.SINGLE
            elif first_word == "Multiple":
                patient_history["venousClotsNumberOfOccurances"] = VenousClotOccurrencesOptions.MULTIPLE

            if "PFO" in patient_answer:
                patient_history["venousClotsPfoHasHistory"] = PFOPresenceOptions.POSITIVE
            else:
                patient_history["venousClotsPfoHasHistory"] = PFOPresenceOptions.NEGATIVE

    return patient_history


# Get records using syntrillo_internal_key from srs_form_responses table
def get_srs_healthie_data(healthie_user_id: str, db_manager: SyntrilloDatabaseManager, syntrillo_internal_key: uuid.UUID, healthie_utils: HealthieUtils) -> dict:
    """
    Get the data needed for SRS calculations that is stored in healthie from the healthie user id
    Args:
        healthie_user_id (str): The healthie user id

    Returns:
        dict: The healthie data
        {
            "average_rhr_baseline": average_rhr_baseline,
            "average_rhr_trailing": average_rhr_trailing,
            "average_rhr_prior": "average_rhr_prior",
            "inactivity_hours_answer": inactivity_hours_answer,
            "activity_minutes_answer": activity_minutes_answer,
            "ssq_score": recent_ssq_entry.get("metric_stat"),
        }
    Raises:
        ValueError: If the healthie data is not valid
    """
    try:
        logger.info("Fetching RHR and Activity data from Healthie...")

        # Retreive resting hr from healthie
        rhr_data = get_healthie_metric_data(healthie_utils, healthie_user_id, category=RHR_CATEGORY)
        rhr_metadata = calc_rhr_metadata(rhr_data) if rhr_data else {}

        # Retreive the activity data
        # OLD ACTIVITY DATA RETRIEVAL METHOD --> activity_data = get_healthie_activity_data(db_manager, syntrillo_internal_key)
        hours_sitting_data = get_healthie_metric_data(healthie_utils, healthie_user_id, category=HOURS_SITTING_CATEGORY)
        recent_hours_sitting_entry = hours_sitting_data[-1] if hours_sitting_data else {}

        physical_activity_minutes_data = get_healthie_metric_data(healthie_utils, healthie_user_id, category=PHYSICAL_ACTIVITY_MINS_CATEGORY)
        recent_physical_activity_minutes_entry = physical_activity_minutes_data[-1] if physical_activity_minutes_data else {}

        recent_ssq_data = get_healthie_metric_data(healthie_utils, healthie_user_id, category=SSQ_CATEGORY)
        recent_ssq_entry = recent_ssq_data[-1] if recent_ssq_data else {}

        # None value will be used to indicate that there is no data to calculate the metadata
        # and this will impact the risk score calculation as no data means more attention is needed.
        logger.info("Successfully fetched RHR and Physical Activity data from Healthie...")
        return {
            "average_rhr_baseline": rhr_metadata.get("average_rhr_baseline"),
            "average_rhr_trailing": rhr_metadata.get("average_rhr_trailing"),
            "average_rhr_prior": rhr_metadata.get("average_rhr_prior"),
            "inactivity_hours_answer": recent_hours_sitting_entry.get("metric_stat"),
            "activity_minutes_answer": recent_physical_activity_minutes_entry.get("metric_stat"),
            "ssq_score": recent_ssq_entry.get("metric_stat")
        }

    except Exception as e:
        logger.error(f"Error fetching RHR and/or Physical Activity data from healthie: {e}")
        raise ValueError("Error fetching RHR and/or Physical Activity data from healthie")


def get_healthie_activity_and_inactivity_module_ids(db_manager: SyntrilloDatabaseManager) -> dict:
    """
    This function retreives the module ids for the inactivity and activity questions answered
    on the charting and intake healthie forms.

    Args:
        db_manager (SyntrilloDatabaseManager): The syntrillo database manager
    Returns:

    Raises:
    """

    _, module_id_inactivity_intake = db_manager.get_form_module_ids_by_module_label(INACTIVITY_INTAKE_MODULE_LABEL)
    _, module_id_inactivity_charting = db_manager.get_form_module_ids_by_module_label(INACTIVITY_CHARTING_MODULE_LABEL)

    _, module_id_activity_intake = db_manager.get_form_module_ids_by_module_label(ACTIVITY_INTAKE_MODULE_LABEL)
    _, module_id_activity_charting = db_manager.get_form_module_ids_by_module_label(ACTIVITY_CHARTING_MODULE_LABEL)


    return {
        "module_id_inactivity_intake": module_id_inactivity_intake,
        "module_id_inactivity_charting": module_id_inactivity_charting,
        "module_id_activity_intake": module_id_activity_intake,
        "module_id_activity_charting": module_id_activity_charting
    }


def get_healthie_activity_data(db_manager: SyntrilloDatabaseManager, syntrillo_internal_key: uuid.UUID) -> dict:
    """
    Get the activity data from healthie
    Args:
        healthie_user_id (str): The healthie user id
        db_manager (SyntrilloDatabaseManager): The syntrillo database manager

    Returns:
        inactivity_minutes_answer (dict | None): The patient's inactivity minutes form response answer
    Raises:
        ValueError: If the inactivity minutes answer is not valid
    """

    try:
        logger.info("Fetching activity data from healthie...")

        # Get the module ids for the intake and charting modules
        physical_activity_module_ids = get_healthie_activity_and_inactivity_module_ids(db_manager=db_manager)
        module_id_inactivity_intake = physical_activity_module_ids["module_id_inactivity_intake"]
        module_id_inactivity_charting = physical_activity_module_ids["module_id_inactivity_charting"]
        module_id_activity_intake = physical_activity_module_ids["module_id_activity_intake"]
        module_id_activity_charting = physical_activity_module_ids["module_id_activity_charting"]

        syntrillo_internal_key_str = str(syntrillo_internal_key)

        # Retreive the intake & charting inactivity value based on the module id and healthie user id
        intake_inactivity_hours_answer, intake_updated_at = db_manager.get_patient_form_response_by_module_id(module_id_inactivity_intake, syntrillo_internal_key_str)
        charting_inactivity_hours_answer, charting_updated_at = db_manager.get_patient_form_response_by_module_id(module_id_inactivity_charting, syntrillo_internal_key_str)

        intake_activity_minutes_answer, intake_activity_updated_at = db_manager.get_patient_form_response_by_module_id(module_id_activity_intake, syntrillo_internal_key_str)
        charting_activity_minutes_answer, charting_activity_updated_at = db_manager.get_patient_form_response_by_module_id(module_id_activity_charting, syntrillo_internal_key_str)

        # Use the most recent answer from the intake or charting responses
        if not intake_inactivity_hours_answer and not charting_inactivity_hours_answer:
            return {
                "inactivity_hours_answer": None,
                "activity_minutes_answer": None,
            }
        elif not intake_inactivity_hours_answer:
            inactivity_hours_answer = charting_inactivity_hours_answer
            activity_minutes_answer = charting_activity_minutes_answer
        elif not charting_inactivity_hours_answer:
            inactivity_hours_answer = intake_inactivity_hours_answer
            activity_minutes_answer = intake_activity_minutes_answer
        else:
            inactivity_hours_answer = intake_inactivity_hours_answer if intake_updated_at > charting_updated_at else charting_inactivity_hours_answer
            activity_minutes_answer = intake_activity_minutes_answer if intake_updated_at > charting_updated_at else charting_activity_minutes_answer

        # Convert to int for DB range comparison
        inactivity_hours_answer = float(inactivity_hours_answer)
        activity_minutes_answer = float(activity_minutes_answer)

        logger.info("Successfully fetched activity data from healthie...")
        return {
            "inactivity_hours_answer": inactivity_hours_answer,
            "activity_minutes_answer": activity_minutes_answer,
        }

    except Exception as e:
        logger.error(f"Error fetching activity data from healthie: {e}")
        raise ValueError("Error fetching activity data from healthie")


def get_healthie_metric_data(healthie_utils: HealthieUtils, healthie_user_id: str, page_size: int = 100, category: str = RHR_CATEGORY) -> List[dict]:
    """
    Fetch all metric category data from healthie using the syntrillo_internal_key

    Args:
        healthie_utils (HealthieUtils): The healthie utils
        healthie_user_id (str): The healthie user id
        category (str): The healthie metric category
    Returns:
        all_metric_data (List[dict]): All metric data for the patient and
    """
    logger.info("Fetching RHR data from healthie...")
    try:
        all_metric_data = []
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
                "category": category,
                "type": ENTRY_TYPE,
                "page_size": page_size,
                "sort_by": "created_at::asc"
            }
            if cursor:
                variables["after"] = cursor

            # Retrieve the current set of responses
            response: dict= healthie_utils.run_graphql_query(query=query, variables=variables)
            current_page_data = response.get("entries", [])

            # Append the newest set of responses to output array
            all_metric_data.extend(current_page_data)

            # Check if there are more pages to fetch
            if len(current_page_data) == page_size and current_page_data[-1].get("cursor", None):
                cursor = current_page_data[-1]["cursor"]
            else:
                has_more_pages = False
                logger.info("No more pages to fetch.")

        logger.info(f"Successfully fetched {len(all_metric_data)} metric data points from healthie.")
        return all_metric_data

    except Exception as e:
        logger.error(f"Error fetching metric data from healthie: {e}")
        raise ValueError("Error fetching metric data from healthie")



def calc_rhr_metadata(
    rhr_data: list[dict],
    baseline_num_weeks: int = BASELINE_NUM_WEEKS,
    trailing_num_weeks: int = TRAILING_NUM_WEEKS,
    prior_num_weeks: int = 2
    ) -> dict:
    """
    Calculate the RHR metadata from the rhr_data
    Args:
        rhr_data (list[dict]): The rhr data
        baseline_start (datetime): The baseline start date
        baseline_end (datetime): The baseline end date
    Returns:
        dict: The RHR metadata
    Raises:
        ValueError: If the RHR metadata is not valid
    """
    try:
        logger.info("Calculating RHR metadata...")
        # Convert rhr_data to pandas dataframe
        rhr_df = pd.DataFrame(rhr_data)

        # Clean the rhr_data
        rhr_df = rhr_df.drop(columns=['third_party_source', 'source', 'cursor', 'metric_stat_string', 'category'])
        rhr_df[CREATED_AT] = pd.to_datetime(rhr_df[CREATED_AT], errors='coerce') # ensure the created_at is a datetime

        # BASELINE DATAFRAME
        # Determine the baseline start and end dates
        baseline_start = rhr_df[CREATED_AT].min()
        baseline_end = baseline_start + pd.Timedelta(weeks=baseline_num_weeks)

        # Ensure the baseline dataframe is valid
        baseline_df = get_timeframed_data(rhr_df, baseline_start, baseline_end, TYPE_RHR)
        baseline_average = baseline_df[METRIC_STAT].mean() if not baseline_df.empty else None


        # TRAILING DATAFRAME
        # Determine the trailing start and end dates
        trailing_end = pd.Timestamp.now().tz_localize('UTC').tz_convert('America/New_York')
        trailing_start = trailing_end - pd.Timedelta(weeks=trailing_num_weeks)
        trailing_average = None
        if is_valid_trailing_timeframe_dates(trailing_start, baseline_end):
            trailing_df = get_timeframed_data(rhr_df, trailing_start, trailing_end, TYPE_RHR)
            trailing_average = trailing_df[METRIC_STAT].mean() if not trailing_df.empty else None # Calculate the average trailing for the rhr_data
        else:
            logger.warning("Not enough data to calculate trailing average...")

        # PRIOR DATAFRAME
        # Trailing > Prior > Baseline (this is an addition for the BP dashboard 9/8/25)
        prior_end = trailing_start - pd.Timedelta(days=1) # Get day before start of trailing period
        prior_start = prior_end - pd.Timedelta(weeks=prior_num_weeks)
        prior_average = None
        # Check if the baseline timeframe overlaps with the prior timeframe
        if is_valid_trailing_timeframe_dates(prior_start, baseline_end):
            prior_df = get_timeframed_data(rhr_df, prior_start, prior_end, TYPE_RHR)
            prior_average = prior_df[METRIC_STAT].mean() if not prior_df.empty else None # Calculate the average prior for the rhr_data
        else:
            logger.warning("Not enough data to calculate prior average...")

        logger.info("Successfully calculated RHR metadata...")
        # Return the metadata
        return {
            "average_rhr_baseline": round(baseline_average, 2) if baseline_average else None,
            "average_rhr_trailing": round(trailing_average, 2) if trailing_average else None,
            "average_rhr_prior": round(prior_average, 2) if prior_average else None,
            "baseline_start_date": baseline_start if baseline_start else None,
            "baseline_end_date": baseline_end if baseline_end else None,
            "prior_start_date": prior_start if prior_start else None,
            "prior_end_date": prior_end if prior_end else None,
            "current_start_date": trailing_start if trailing_start else None,
            "current_end_date": trailing_end if trailing_end else None,
        }

    except Exception as e:
        logger.error(f"Error calculating RHR metadata: {e}")
        raise ValueError("Error calculating RHR metadata")

def calc_pulse_metadata(
    pulse_data: list[dict],
    baseline_num_weeks: int = BASELINE_NUM_WEEKS,
    trailing_num_weeks: int = TRAILING_NUM_WEEKS,
    prior_num_weeks: int = 2
    ) -> dict:
    """
    Calculate the RHR metadata from the rhr_data
    Args:
        rhr_data (list[dict]): The rhr data
        baseline_start (datetime): The baseline start date
        baseline_end (datetime): The baseline end date
    Returns:
        dict: The RHR metadata
    Raises:
        ValueError: If the RHR metadata is not valid
    """
    try:
        logger.info("Calculating RHR metadata...")
        # Convert pulse_data to pandas dataframe
        pulse_df = pd.DataFrame(pulse_data)

        # Clean the pulse_data
        pulse_df = pulse_df.drop(columns=['third_party_source', 'source', 'cursor', 'metric_stat_string', 'category'])
        pulse_df[CREATED_AT] = pd.to_datetime(pulse_df[CREATED_AT], errors='coerce') # ensure the created_at is a datetime
        # BASELINE DATAFRAME
        # Determine the baseline start and end dates
        baseline_start = pulse_df[CREATED_AT].min()
        baseline_end = baseline_start + pd.Timedelta(weeks=baseline_num_weeks)

        # Ensure the baseline dataframe is valid
        baseline_df = get_timeframed_data(pulse_df, baseline_start, baseline_end, TYPE_PULSE)
        baseline_average = baseline_df[METRIC_STAT].mean() if not baseline_df.empty else None


        # TRAILING DATAFRAME
        # Determine the trailing start and end dates
        trailing_end = pd.Timestamp.now().tz_localize('UTC').tz_convert('America/New_York')
        trailing_start = trailing_end - pd.Timedelta(weeks=trailing_num_weeks)
        trailing_average = None
        if is_valid_trailing_timeframe_dates(trailing_start, baseline_end):
            trailing_df = get_timeframed_data(pulse_df, trailing_start, trailing_end, TYPE_PULSE)
            trailing_average = trailing_df[METRIC_STAT].mean() if not trailing_df.empty else None # Calculate the average trailing for the rhr_data
        else:
            logger.warning("Not enough data to calculate trailing average...")

        # PRIOR DATAFRAME
        # Trailing > Prior > Baseline (this is an addition for the BP dashboard 9/8/25)
        prior_end = trailing_start - pd.Timedelta(days=1) # Get day before start of trailing period
        prior_start = prior_end - pd.Timedelta(weeks=prior_num_weeks)
        prior_average = None
        # Check if the baseline timeframe overlaps with the prior timeframe
        if is_valid_trailing_timeframe_dates(prior_start, baseline_end):
            prior_df = get_timeframed_data(pulse_df, prior_start, prior_end, TYPE_PULSE)
            prior_average = prior_df[METRIC_STAT].mean() if not prior_df.empty else None # Calculate the average prior for the rhr_data
        else:
            logger.warning("Not enough data to calculate prior average...")

        logger.info("Successfully calculated RHR metadata...")
        # Return the metadata
        return {
            "average_rhr_baseline": round(baseline_average, 2) if baseline_average else None,
            "average_rhr_trailing": round(trailing_average, 2) if trailing_average else None,
            "average_rhr_prior": round(prior_average, 2) if prior_average else None,
            "baseline_start_date": baseline_start if baseline_start else None,
            "baseline_end_date": baseline_end if baseline_end else None,
            "prior_start_date": prior_start if prior_start else None,
            "prior_end_date": prior_end if prior_end else None,
            "current_start_date": trailing_start if trailing_start else None,
            "current_end_date": trailing_end if trailing_end else None,
        }

    except Exception as e:
        logger.error(f"Error calculating RHR metadata: {e}")
        raise ValueError("Error calculating RHR metadata")


def get_srs_response_data(syntrillo_internal_key: uuid.UUID, db_manager: SyntrilloDatabaseManager) -> Union[SRSFormResponse, None]:
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
        {
            "trailing_hr_variability": trailing_hr_variability,
            "trailing_hr_average": trailing_hr_average,
        }
    Raises:
        ValueError: If the hr data is not valid
    """
    try:
        logger.info("Fetching Tenovi HR data...")
        hr_measurements, _ = db_manager.get_latest_measurements(metric_name=PULSE_METRIC_NAME)
        if len(hr_measurements) == 0:
            logger.warning("No Tenovi HR data found for the patient ...")
            return {
                "trailing_hr_variability": None,
                "trailing_hr_average": None,
            }
        hr_df = pd.DataFrame(hr_measurements)

        # Convert timestamp to datetime
        hr_df[TIMESTAMP] = pd.to_datetime(hr_df[TIMESTAMP], errors='coerce')
        # Convert to numeric from string, value_1 is the hr data, value_2 is always 0
        hr_df[VALUE_1] = pd.to_numeric(hr_df[VALUE_1], errors='coerce')

        # Calculate variability for trailing 4 weeks HR data
        # Calculate the trailing start and end dates
        trailing_end = pd.Timestamp.now().tz_localize('UTC').tz_convert('America/New_York')
        trailing_start = trailing_end - pd.Timedelta(weeks=TRAILING_NUM_WEEKS)

        trailing_df = get_timeframed_data(hr_df, trailing_start, trailing_end, TYPE_HR)
        trailing_hr_average = trailing_df[VALUE_1].mean() if not trailing_df.empty else None
        trailing_hr_variability = trailing_df[VALUE_1].std() if not trailing_df.empty else None

        logger.info("Successfully fetched Tenovi HR data...")
        return {
            "trailing_hr_variability": round(trailing_hr_variability, 2) if trailing_hr_variability else None,
            "trailing_hr_average": round(trailing_hr_average, 2) if trailing_hr_average else None,
        }

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
                    PEAK_AVG_SBP: trailing_bp_metadata[PEAK_SBP],
                },
                BASELINE: {
                    AVERAGE: baseline_bp_metadata[AVG_SBP],
                },
            },
            DIASTOLIC: {
                TRAILING: {
                    AVERAGE: trailing_bp_metadata[AVG_DBP],
                },
                BASELINE: {
                    AVERAGE: baseline_bp_metadata[AVG_DBP],
                },
            },
        }
    Raises:
        ValueError: If the bp metadata is not valid
    """
    try:
        logger.info("Beginning Tenovi BP data aggregation...")
        bp_analysis = BloodPressureAnalysis(syntrillo_internal_key)
        bp_df, _ = bp_analysis.get_blood_pressure_dataframe()
        if bp_df is None or bp_df.empty:
            return {
                SYSTOLIC: {
                    TRAILING: {
                        SBP_COUNT_175: None,
                        VARIABILITY: None,
                        AVERAGE: None,
                        PEAK_AVG_SBP: None,
                    },
                    BASELINE: {
                        AVERAGE: None,
                        VARIABILITY: None,
                        PEAK_AVG_SBP: None,
                    },
                },
                DIASTOLIC: {
                    TRAILING: {
                        AVERAGE: None,
                    },
                    BASELINE: {
                        AVERAGE: None,
                    },
                }
            }
        logger.info("Successfully fetched Tenovi BP data...")

        # Get baseline start date as it used in both baseline and trailing dataframes
        # Baseline start date is the first timestamp in the bp_df
        baseline_start = bp_df[TIMESTAMP_LOCAL].min()

        # Get the baseline and trailing dataframes
        logger.info("Getting baseline and trailing dataframes...")
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
            # raise ValueError("Trailing data is not valid")
            return None

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
                    PEAK_AVG_SBP: trailing_bp_metadata[PEAK_SBP],
                },
                BASELINE: {
                    AVERAGE: baseline_bp_metadata[AVG_SBP],
                    VARIABILITY: baseline_bp_metadata[SBP_SD],
                    PEAK: baseline_bp_metadata[PEAK_SBP],
                },
            },
            DIASTOLIC: {
                TRAILING: {
                    AVERAGE: trailing_bp_metadata[AVG_DBP],
                },
                BASELINE: {
                    AVERAGE: baseline_bp_metadata[AVG_DBP],
                },
            },
        }
    Raises:
        ValueError: If the bp metadata is not valid
    """
    try:
        logger.info("Calculating bp metadata...")
        # Calculate the metadata for the trailing dataframe
        trailing_bp_metadata = bp_analysis.calculate_timeframe_metadata(trailing_bp_dataframe) if trailing_bp_dataframe is not None else {}
        # NOT CURRENTLY USED BUT CAN BE USED IN FUTURE – baseline_bp_metadata = bp_analysis.calculate_timeframe_metadata(baseline_bp_dataframe)
        baseline_bp_metadata = bp_analysis.calculate_timeframe_metadata(baseline_bp_dataframe)

        # Trim the metadata to only include the necessary data for SRS calculation
        trimmed_bp_metadata = {
            SYSTOLIC: {
                TRAILING: {
                    SBP_COUNT_175: float(trailing_bp_metadata[SBP_COUNT_175]) if SBP_COUNT_175 in trailing_bp_metadata else None, # Considered the "PEAK" BP value for SRS
                    VARIABILITY: trailing_bp_metadata[SBP_SD] if SBP_SD in trailing_bp_metadata else None,
                    AVERAGE: trailing_bp_metadata[AVG_SBP] if AVG_SBP in trailing_bp_metadata else None,
                    PEAK_AVG_SBP: trailing_bp_metadata[PEAK_SBP] if PEAK_SBP in trailing_bp_metadata else None,
                },
                BASELINE: {
                    AVERAGE: baseline_bp_metadata[AVG_SBP],
                    VARIABILITY: baseline_bp_metadata[SBP_SD],
                    PEAK_AVG_SBP: baseline_bp_metadata[PEAK_SBP],
                },
            },
            DIASTOLIC: {
                TRAILING: {
                    AVERAGE: trailing_bp_metadata[AVG_DBP] if AVG_DBP in trailing_bp_metadata else None,
                },
                BASELINE: {
                    AVERAGE: baseline_bp_metadata[AVG_DBP],
                },
            },
        }
        logger.info("Successfully calculated bp metadata...")
        return trimmed_bp_metadata

    except Exception as e:
        logger.error(f"Error calculating bp metadata: {e}")
        raise ValueError("Error calculating bp metadata")


def get_timeframed_data(dataframe: pd.DataFrame, timeframe_start: datetime, timeframe_end: datetime, measurement_type: str) -> pd.DataFrame:
    """
    Get the timeframed data from the dataframe
    Args:
        dataframe (pd.DataFrame): The dataframe
        timeframe_start (datetime): The start date of the timeframe
        timeframe_end (datetime): The end date of the timeframe
        measurement_type (str): The type of measurement

    Returns:
        pd.DataFrame: The timeframed data
    Raises:
        ValueError: If the timeframed data is not valid
    """
    try:
        if measurement_type == TYPE_BP:
            timeframe_df = dataframe[(dataframe[TIMESTAMP_LOCAL] >= timeframe_start) & (dataframe[TIMESTAMP_LOCAL] < timeframe_end)]
        elif measurement_type == TYPE_RHR or measurement_type == TYPE_PULSE:
            timeframe_df = dataframe[(dataframe[CREATED_AT] >= timeframe_start) & (dataframe[CREATED_AT] < timeframe_end)]
        elif measurement_type == TYPE_HR:
            timeframe_df = dataframe[(dataframe[TIMESTAMP] >= timeframe_start) & (dataframe[TIMESTAMP] < timeframe_end)]
        else:
            logger.error(f"Invalid type: {measurement_type}")
            raise ValueError(f"Invalid type: {measurement_type}")

        if not is_valid_timeframe_num_measurements(timeframe_df):
            logger.warning(f"Timeframed data is not valid for {measurement_type}...")
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

def get_lab_data(healthie_utils: HealthieUtils, healthie_user_id: str) -> LabData:
    """
    Retieves all the lab relevant data (metrics section) from Healthie.

    Args:
        healthie_utils (HealthieUtils): The healthie utils
        healthie_user_id (str): The healthie user id
    Returns:
        lab_data (LabData):
    Raises:
        e (Exception): General error exception
    """
    try:
        # 1. Get lab data from Healthie
        ldl_data = get_healthie_metric_data(healthie_utils, healthie_user_id, category=LDL_CATEGORY)
        hdl_data = get_healthie_metric_data(healthie_utils, healthie_user_id, category=HDL_CATEGORY)
        creatintine_data = get_healthie_metric_data(healthie_utils, healthie_user_id, category=CREATINTINE_CATEGORY)
        hgA1c_data = get_healthie_metric_data(healthie_utils, healthie_user_id, category=HGA1C_CATEGORY)
        hsCRP_data = get_healthie_metric_data(healthie_utils, healthie_user_id, category=HSCRP_CATEGORY)
        hemoglobin_data = get_healthie_metric_data(healthie_utils, healthie_user_id, category=HEMOGLOBIN_CATEGORY)

        recent_ldl_entry = ldl_data[-1] if ldl_data else {}
        recent_hdl_entry = hdl_data[-1] if hdl_data else {}
        recent_creatintine_entry = creatintine_data[-1] if creatintine_data else {}
        recent_hgA1c_entry = hgA1c_data[-1] if hgA1c_data else {}
        recent_hsCRP_entry = hsCRP_data[-1] if hsCRP_data else {}
        recent_hemoglobin_entry = hemoglobin_data[-1] if hemoglobin_data else {}

        lab_data_vals = {
            "ldl_value": recent_ldl_entry.get("metric_stat"),
            "hdl_value": recent_hdl_entry.get("metric_stat"),
            "creatintine_value": recent_creatintine_entry.get("metric_stat"),
            "hgA1c_value": recent_hgA1c_entry.get("metric_stat"),
            "hsCRP_value": recent_hsCRP_entry.get("metric_stat"),
            "hemoglobin_value": recent_hemoglobin_entry.get("metric_stat"),
        }

        # TODO -- 2. Get Zus lab data from internal DB

        # Load data into LabData object
        lab_data = LabData.model_validate(lab_data_vals)

        return lab_data

    except Exception as e:
        logger.error(f"Error while retrieving lab data for SRS: {e}")
        raise e



# if __name__ == "__main__":
    # syntrillo_internal_key = uuid.UUID("ff8d04c4-9307-4171-888b-447047d5fa36")
    # data = aggregate_data(syntrillo_internal_key)
    # syntrillo_internal_key = uuid.UUID("41ce2a96-a404-497c-835e-236a0f972a9d") # Bob Barker – id 2315391
    # data = aggregate_data(syntrillo_internal_key=syntrillo_internal_key, is_first=True)
    # print(data)

    # healthie_user_id = "2315391"
    # healthie_utils = HealthieUtils()
    # get_lab_data(healthie_utils, healthie_user_id)

    # print(json.dumps(get_patient_history_data(healthie_user_id="2315391"), indent=4))
