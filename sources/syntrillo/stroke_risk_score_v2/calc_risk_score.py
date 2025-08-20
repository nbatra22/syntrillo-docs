import uuid
import numpy as np

from syntrillo.system.logger import logger
from syntrillo.remote_monitoring.syntrillo_database_manager import SyntrilloDatabaseManager
from syntrillo.stroke_risk_score_v2.agg_data import aggregate_data
from syntrillo.stroke_risk_score_v2.constants import (
    LOW_VALUE,
    LOW_INTERMEDIATE_VALUE,
    INTERMEDIATE_HIGH_VALUE,
    HIGH_VALUE,
    MODERATE_EFFICACY,
    HIGH_EFFICACY,
    AVG_SBP,
    RHR,
    HEMOGLOBIN_A1C,
    PHYSICAL_INACTIVITY,
    PHYSICAL_ACTIVITY,
    CIGARETTE_USE,
    ALCOHOL_USE,
    MARIJUANA_USE,
    SBP_STD,
    AVG_PEAK_SBP,
    AVG_DBP,
    CREATININE,
    VALUE,
    TREATMENT_OPTIM,
    TREATMENT_EFFICACY,
    GENDER,
    UNKNOWN,
)
from syntrillo.bp_analysis.constants import (
    SYSTOLIC,
    DIASTOLIC,
    SBP_COUNT_175,
    AVERAGE,
    VARIABILITY,
    TRAILING
)
from syntrillo.stroke_risk_score_v2.models.srs_form import (
    AnemiaSeverityOptions,
    ArterialClotOccurrencesOptions,
    CADTypeOptions,
    EjectionFractionOptions,
    HDLLevelOptions,
    LDLLevelOptions,
    LikelihoodOfTIAOptions,
    NumberOfStrokesOptions,
    OSASeverityOptions,
    PFOPresenceOptions,
    SRSFormResponse,
    StenosisPercentageOptions,
    StrokeMechanismOptions,
    TriglyceridesLevelOptions,
    VenousClotOccurrencesOptions,
)
from syntrillo.stroke_risk_score_v2.models.treatment_compliance import TreatmentComplianceOptions

# Dependent Risk Factors
weighting = {
    VALUE: {
        LOW_VALUE: 1.25,
        LOW_INTERMEDIATE_VALUE: 1.50,
        INTERMEDIATE_HIGH_VALUE: 1.75,
        HIGH_VALUE: 2.25,
    },
    TREATMENT_EFFICACY: {
        MODERATE_EFFICACY: 0.35,
        HIGH_EFFICACY: 0.70,
    },
    TREATMENT_OPTIM: {
        TreatmentComplianceOptions.OPTIMIZED: 1.0,
        TreatmentComplianceOptions.PARTIALLY_OPTIMIZED: 0.5,
        TreatmentComplianceOptions.NOT_OPTIMIZED: 0.0,
        # None: 0.0,
    }
}

EXCLUDED_CATEGORIES = {PHYSICAL_ACTIVITY, GENDER}

def calculate_risk_score(syntrillo_internal_key: uuid.UUID) -> tuple[float, dict, float]:
    """
    Calculate the risk score for a given syntrillo internal key

    Args:
        syntrillo_internal_key (uuid.UUID): The syntrillo internal key

    Returns:
        tuple[float, dict]: The risk score and the aggregated data
    """
    try:
        agg_data = aggregate_data(syntrillo_internal_key)
        db_manager = SyntrilloDatabaseManager(syntrillo_internal_key)

        independent_risk_factor_value, stroke_priority_score_total = calculate_independent_srs_values(agg_data, db_manager)
        dependent_risk_values = calculate_dependent_risk_factors(agg_data)

        final_dependent_score = dependent_risk_values["final_dependent_score"]

        total_srs = final_dependent_score * independent_risk_factor_value
        final_srs = round(total_srs**0.70, 2)

        total_stroke_priority_score = final_dependent_score * stroke_priority_score_total
        final_stroke_priority_score = round(total_stroke_priority_score**0.70, 2)

        return final_srs, agg_data, final_stroke_priority_score
    except Exception as e:
        logger.error(f"Error calculating risk score: {e}")
        return None, None, None



def calculate_dependent_risk_factors(agg_data: dict) -> dict:
    """
    Calculates the risk score values associated with dependent risk factors.

    Args:
        agg_data (dict): The aggregated data
    Returns:
        dict: The risk score values associated with dependent risk factors.
    Raises:
        Exception: If an error occurs while calculating the dependent risk factors.
    """
    try:
        logger.info(f"Calculating dependent risk factors...")
        srs_response_forms = agg_data.get("srs_response_data", None)
        most_recent_srs_form_response: SRSFormResponse = srs_response_forms[0]
        compliance_data = most_recent_srs_form_response.compliance

        final_dependent_score = 1.0

        # History of ischemia
        if most_recent_srs_form_response.HasPreviousStroke:
            if most_recent_srs_form_response.NumberOfStrokes == NumberOfStrokesOptions.ONE:
                if most_recent_srs_form_response.LatestStrokeMechanism == StrokeMechanismOptions.SMALL_VESSEL:
                    dependent_risk_factor_value = weighting[VALUE][HIGH_VALUE]
                    dependent_efficacy_value = weighting[TREATMENT_EFFICACY][HIGH_EFFICACY]
                elif most_recent_srs_form_response.LatestStrokeMechanism == StrokeMechanismOptions.LARGE_VESSEL:
                    dependent_risk_factor_value = weighting[VALUE][HIGH_VALUE]
                    dependent_efficacy_value = weighting[TREATMENT_EFFICACY][HIGH_EFFICACY]
                elif most_recent_srs_form_response.LatestStrokeMechanism == StrokeMechanismOptions.CARDIOEMBOLIC:
                    dependent_risk_factor_value = weighting[VALUE][HIGH_VALUE]
                    dependent_efficacy_value = weighting[TREATMENT_EFFICACY][HIGH_EFFICACY]
                elif most_recent_srs_form_response.LatestStrokeMechanism == StrokeMechanismOptions.CRYPTOGENIC:
                    dependent_risk_factor_value = weighting[VALUE][HIGH_VALUE]
                    dependent_efficacy_value = weighting[TREATMENT_EFFICACY][HIGH_EFFICACY]
                elif most_recent_srs_form_response.LatestStrokeMechanism == StrokeMechanismOptions.HYPERCOAGULABLE:
                    dependent_risk_factor_value = weighting[VALUE][HIGH_VALUE]
                    dependent_efficacy_value = weighting[TREATMENT_EFFICACY][HIGH_EFFICACY]
                elif most_recent_srs_form_response.LatestStrokeMechanism == StrokeMechanismOptions.STRUCTURAL:
                    dependent_risk_factor_value = weighting[VALUE][HIGH_VALUE]
                    dependent_efficacy_value = weighting[TREATMENT_EFFICACY][HIGH_EFFICACY]

            elif most_recent_srs_form_response.NumberOfStrokes == NumberOfStrokesOptions.MULTIPLE:
                if most_recent_srs_form_response.LatestStrokeMechanism == StrokeMechanismOptions.SMALL_VESSEL:
                    dependent_risk_factor_value = weighting[VALUE][HIGH_VALUE]
                    dependent_efficacy_value = weighting[TREATMENT_EFFICACY][HIGH_EFFICACY]
                elif most_recent_srs_form_response.LatestStrokeMechanism == StrokeMechanismOptions.LARGE_VESSEL:
                    dependent_risk_factor_value = weighting[VALUE][HIGH_VALUE]
                    dependent_efficacy_value = weighting[TREATMENT_EFFICACY][HIGH_EFFICACY]
                elif most_recent_srs_form_response.LatestStrokeMechanism == StrokeMechanismOptions.CRYPTOGENIC:
                    dependent_risk_factor_value = weighting[VALUE][HIGH_VALUE]
                    dependent_efficacy_value = weighting[TREATMENT_EFFICACY][HIGH_EFFICACY]
                elif most_recent_srs_form_response.LatestStrokeMechanism == StrokeMechanismOptions.HYPERCOAGULABLE:
                    dependent_risk_factor_value = weighting[VALUE][HIGH_VALUE]
                    dependent_efficacy_value = weighting[TREATMENT_EFFICACY][HIGH_EFFICACY]
                elif most_recent_srs_form_response.LatestStrokeMechanism == StrokeMechanismOptions.STRUCTURAL:
                    dependent_risk_factor_value = weighting[VALUE][HIGH_VALUE]
                    dependent_efficacy_value = weighting[TREATMENT_EFFICACY][MODERATE_EFFICACY]

            dependent_optimization_value = weighting[TREATMENT_OPTIM][compliance_data.strokeCompliance]
            final_dependent_score *= ((dependent_risk_factor_value-1)*(1-(dependent_efficacy_value*dependent_optimization_value)))+1

        if most_recent_srs_form_response.ScreenedForTIA and most_recent_srs_form_response.LikelihoodOfTIA == LikelihoodOfTIAOptions.HIGH_LIKELIHOOD:
            if most_recent_srs_form_response.TIAMechanism == StrokeMechanismOptions.SMALL_VESSEL:
                dependent_risk_factor_value = weighting[VALUE][HIGH_VALUE]
                dependent_efficacy_value = weighting[TREATMENT_EFFICACY][HIGH_EFFICACY]
            elif most_recent_srs_form_response.TIAMechanism == StrokeMechanismOptions.LARGE_VESSEL:
                dependent_risk_factor_value = weighting[VALUE][HIGH_VALUE]
                dependent_efficacy_value = weighting[TREATMENT_EFFICACY][HIGH_EFFICACY]
            elif most_recent_srs_form_response.TIAMechanism == StrokeMechanismOptions.CRYPTOGENIC:
                dependent_risk_factor_value = weighting[VALUE][HIGH_VALUE]
                dependent_efficacy_values += weighting[TREATMENT_EFFICACY][HIGH_EFFICACY]
            elif most_recent_srs_form_response.TIAMechanism == StrokeMechanismOptions.HYPERCOAGULABLE:
                dependent_risk_factor_value = weighting[VALUE][HIGH_VALUE]
                dependent_efficacy_value = weighting[TREATMENT_EFFICACY][HIGH_EFFICACY]
            elif most_recent_srs_form_response.TIAMechanism == StrokeMechanismOptions.CARDIOEMBOLIC:
                dependent_risk_factor_value = weighting[VALUE][HIGH_VALUE]
                dependent_efficacy_value = weighting[TREATMENT_EFFICACY][HIGH_EFFICACY]
            elif most_recent_srs_form_response.TIAMechanism == StrokeMechanismOptions.STRUCTURAL:
                dependent_risk_factor_value = weighting[VALUE][HIGH_VALUE]
                dependent_efficacy_value = weighting[TREATMENT_EFFICACY][MODERATE_EFFICACY]

            dependent_optimization_value = weighting[TREATMENT_OPTIM][compliance_data.tiaCompliance]
            final_dependent_score *= ((dependent_risk_factor_value-1)*(1-(dependent_efficacy_value*dependent_optimization_value)))+1

        if most_recent_srs_form_response.HasPriorHeadCT and most_recent_srs_form_response.ChronicInfarctPresent:
            if most_recent_srs_form_response.ChronicInfarctMechanism == StrokeMechanismOptions.SMALL_VESSEL:
                dependent_risk_factor_value = weighting[VALUE][HIGH_VALUE]
                dependent_efficacy_value = weighting[TREATMENT_EFFICACY][HIGH_EFFICACY]
            elif most_recent_srs_form_response.ChronicInfarctMechanism == StrokeMechanismOptions.LARGE_VESSEL:
                dependent_risk_factor_value = weighting[VALUE][HIGH_VALUE]
                dependent_efficacy_value = weighting[TREATMENT_EFFICACY][HIGH_EFFICACY]
            elif most_recent_srs_form_response.ChronicInfarctMechanism == StrokeMechanismOptions.CRYPTOGENIC:
                dependent_risk_factor_value = weighting[VALUE][HIGH_VALUE]
                dependent_efficacy_value = weighting[TREATMENT_EFFICACY][HIGH_EFFICACY]
            elif most_recent_srs_form_response.ChronicInfarctMechanism == StrokeMechanismOptions.HYPERCOAGULABLE:
                dependent_risk_factor_value = weighting[VALUE][HIGH_VALUE]
                dependent_efficacy_value = weighting[TREATMENT_EFFICACY][HIGH_EFFICACY]
            elif most_recent_srs_form_response.ChronicInfarctMechanism == StrokeMechanismOptions.CARDIOEMBOLIC:
                dependent_risk_factor_value = weighting[VALUE][HIGH_VALUE]
                dependent_efficacy_value = weighting[TREATMENT_EFFICACY][HIGH_EFFICACY]
            elif most_recent_srs_form_response.ChronicInfarctMechanism == StrokeMechanismOptions.STRUCTURAL:
                dependent_risk_factor_value = weighting[VALUE][HIGH_VALUE]
                dependent_efficacy_value = weighting[TREATMENT_EFFICACY][MODERATE_EFFICACY]

            dependent_optimization_value = weighting[TREATMENT_OPTIM][compliance_data.chronicInfarctCompliance]
            final_dependent_score *= ((dependent_risk_factor_value-1)*(1-(dependent_efficacy_value*dependent_optimization_value)))+1

        if most_recent_srs_form_response.HistoryOfAtrialFibrillation:
            dependent_risk_factor_value = weighting[VALUE][HIGH_VALUE]
            dependent_efficacy_value = weighting[TREATMENT_EFFICACY][HIGH_EFFICACY]

            dependent_optimization_value = weighting[TREATMENT_OPTIM][compliance_data.atrialFibrillationCompliance]
            final_dependent_score *= ((dependent_risk_factor_value-1)*(1-(dependent_efficacy_value*dependent_optimization_value)))+1

        if most_recent_srs_form_response.HistoryOfIronDeficiencyAnemia:
            if most_recent_srs_form_response.AnemiaSeverity == AnemiaSeverityOptions.MILD:
                dependent_risk_factor_value = weighting[VALUE][LOW_VALUE]
                dependent_efficacy_value = weighting[TREATMENT_EFFICACY][MODERATE_EFFICACY]
            elif most_recent_srs_form_response.AnemiaSeverity == AnemiaSeverityOptions.SEVERE:
                dependent_risk_factor_value = weighting[VALUE][LOW_INTERMEDIATE_VALUE]
                dependent_efficacy_value = weighting[TREATMENT_EFFICACY][MODERATE_EFFICACY]

            dependent_optimization_value = weighting[TREATMENT_OPTIM][compliance_data.ironDeficiencyAnemiaCompliance]
            final_dependent_score *= ((dependent_risk_factor_value-1)*(1-(dependent_efficacy_value*dependent_optimization_value)))+1

        if most_recent_srs_form_response.HistoryOfArterialClots:
            if most_recent_srs_form_response.ArterialClotOccurrences == ArterialClotOccurrencesOptions.SINGLE_PRIOR_EVENT:
                dependent_risk_factor_value = weighting[VALUE][LOW_INTERMEDIATE_VALUE]
                dependent_efficacy_value = weighting[TREATMENT_EFFICACY][MODERATE_EFFICACY]
            elif most_recent_srs_form_response.ArterialClotOccurrences == ArterialClotOccurrencesOptions.MULTIPLE_PRIOR_EVENTS:
                dependent_risk_factor_value = weighting[VALUE][INTERMEDIATE_HIGH_VALUE]
                dependent_efficacy_value = weighting[TREATMENT_EFFICACY][MODERATE_EFFICACY]

            dependent_optimization_value = weighting[TREATMENT_OPTIM][compliance_data.arterialClotsCompliance]
            final_dependent_score *= ((dependent_risk_factor_value-1)*(1-(dependent_efficacy_value*dependent_optimization_value)))+1

        if most_recent_srs_form_response.HistoryOfVenousClots:
            if most_recent_srs_form_response.PFOPresence == PFOPresenceOptions.POSITIVE:
                if most_recent_srs_form_response.VenousClotOccurrences == VenousClotOccurrencesOptions.SINGLE:
                    dependent_risk_factor_value = weighting[VALUE][LOW_INTERMEDIATE_VALUE]
                    dependent_efficacy_value = weighting[TREATMENT_EFFICACY][MODERATE_EFFICACY]
                elif most_recent_srs_form_response.VenousClotOccurrences == VenousClotOccurrencesOptions.MULTIPLE:
                    dependent_risk_factor_value = weighting[VALUE][INTERMEDIATE_HIGH_VALUE]
                    dependent_efficacy_value = weighting[TREATMENT_EFFICACY][MODERATE_EFFICACY]
            elif most_recent_srs_form_response.PFOPresence == PFOPresenceOptions.UNKNOWN:
                if most_recent_srs_form_response.VenousClotOccurrences == VenousClotOccurrencesOptions.SINGLE:
                    dependent_risk_factor_value = weighting[VALUE][LOW_VALUE]
                    dependent_efficacy_value = weighting[TREATMENT_EFFICACY][MODERATE_EFFICACY]
                elif most_recent_srs_form_response.VenousClotOccurrences == VenousClotOccurrencesOptions.MULTIPLE:
                    dependent_risk_factor_value = weighting[VALUE][LOW_VALUE]
                    dependent_efficacy_value = weighting[TREATMENT_EFFICACY][MODERATE_EFFICACY]

            dependent_optimization_value = weighting[TREATMENT_OPTIM][compliance_data.venousClotsCompliance]
            final_dependent_score *= ((dependent_risk_factor_value-1)*(1-(dependent_efficacy_value*dependent_optimization_value)))+1

        if most_recent_srs_form_response.HistoryOfCHF:
            if most_recent_srs_form_response.EjectionFraction == EjectionFractionOptions.LESS_THAN_OR_EQUAL_40:
                dependent_risk_factor_value = weighting[VALUE][INTERMEDIATE_HIGH_VALUE]
                dependent_efficacy_value = weighting[TREATMENT_EFFICACY][MODERATE_EFFICACY]
            elif most_recent_srs_form_response.EjectionFraction == EjectionFractionOptions.GREATER_THAN_40:
                dependent_risk_factor_value = weighting[VALUE][LOW_INTERMEDIATE_VALUE]
                dependent_efficacy_value = weighting[TREATMENT_EFFICACY][MODERATE_EFFICACY]
            elif most_recent_srs_form_response.EjectionFraction == EjectionFractionOptions.UNKNOWN:
                dependent_risk_factor_value = weighting[VALUE][LOW_INTERMEDIATE_VALUE]
                dependent_efficacy_value = weighting[TREATMENT_EFFICACY][MODERATE_EFFICACY]

            dependent_optimization_value = weighting[TREATMENT_OPTIM][compliance_data.chfCompliance]
            final_dependent_score *= ((dependent_risk_factor_value-1)*(1-(dependent_efficacy_value*dependent_optimization_value)))+1

        if most_recent_srs_form_response.HistoryOfCarotidStenosis:
            if most_recent_srs_form_response.StenosisPercentage == StenosisPercentageOptions.FIFTY_TO_SEVENTY:
                dependent_risk_factor_value = weighting[VALUE][LOW_INTERMEDIATE_VALUE]
                dependent_efficacy_value = weighting[TREATMENT_EFFICACY][HIGH_EFFICACY]
            elif most_recent_srs_form_response.StenosisPercentage == StenosisPercentageOptions.GREATER_THAN_SEVENTY:
                dependent_risk_factor_value = weighting[VALUE][HIGH_VALUE]
                dependent_efficacy_value = weighting[TREATMENT_EFFICACY][HIGH_EFFICACY]
            elif most_recent_srs_form_response.StenosisPercentage == StenosisPercentageOptions.UNKNOWN:
                dependent_risk_factor_value = weighting[VALUE][INTERMEDIATE_HIGH_VALUE]
                dependent_efficacy_value = weighting[TREATMENT_EFFICACY][HIGH_EFFICACY]

            dependent_optimization_value = weighting[TREATMENT_OPTIM][compliance_data.carotidStenosisCompliance]
            final_dependent_score *= ((dependent_risk_factor_value-1)*(1-(dependent_efficacy_value*dependent_optimization_value)))+1

        if most_recent_srs_form_response.HistoryOfOSA:
            if most_recent_srs_form_response.OSASeverity == OSASeverityOptions.MILD:
                dependent_risk_factor_value = weighting[VALUE][LOW_VALUE]
                dependent_efficacy_value = weighting[TREATMENT_EFFICACY][HIGH_EFFICACY]
            elif most_recent_srs_form_response.OSASeverity == OSASeverityOptions.MODERATE:
                dependent_risk_factor_value = weighting[VALUE][LOW_INTERMEDIATE_VALUE]
                dependent_efficacy_value = weighting[TREATMENT_EFFICACY][HIGH_EFFICACY]
            elif most_recent_srs_form_response.OSASeverity == OSASeverityOptions.SEVERE:
                dependent_risk_factor_value = weighting[VALUE][INTERMEDIATE_HIGH_VALUE]
                dependent_efficacy_value = weighting[TREATMENT_EFFICACY][HIGH_EFFICACY]
            elif most_recent_srs_form_response.OSASeverity == OSASeverityOptions.UNKNOWN:
                dependent_risk_factor_value = weighting[VALUE][LOW_INTERMEDIATE_VALUE]
                dependent_efficacy_value = weighting[TREATMENT_EFFICACY][HIGH_EFFICACY]

            dependent_optimization_value = weighting[TREATMENT_OPTIM][compliance_data.osaCompliance]
            final_dependent_score *= ((dependent_risk_factor_value-1)*(1-(dependent_efficacy_value*dependent_optimization_value)))+1

        if most_recent_srs_form_response.HistoryOfValvularHeartDisease:
            dependent_risk_factor_value = weighting[VALUE][INTERMEDIATE_HIGH_VALUE]
            dependent_efficacy_value = weighting[TREATMENT_EFFICACY][HIGH_EFFICACY]

            dependent_optimization_value = weighting[TREATMENT_OPTIM][compliance_data.valvularHeartDiseaseCompliance]
            final_dependent_score *= ((dependent_risk_factor_value-1)*(1-(dependent_efficacy_value*dependent_optimization_value)))+1

        if most_recent_srs_form_response.HistoryOfCAD:
            if most_recent_srs_form_response.CADType == CADTypeOptions.SYMPTOMATIC_MULTI_OR_SINGLE_VESSEL:
                dependent_risk_factor_value = weighting[VALUE][INTERMEDIATE_HIGH_VALUE]
                dependent_efficacy_value = weighting[TREATMENT_EFFICACY][MODERATE_EFFICACY]
            elif most_recent_srs_form_response.CADType == CADTypeOptions.ASYMPTOMATIC_MULTIVESSEL:
                dependent_risk_factor_value = weighting[VALUE][INTERMEDIATE_HIGH_VALUE]
                dependent_efficacy_value = weighting[TREATMENT_EFFICACY][MODERATE_EFFICACY]
            elif most_recent_srs_form_response.CADType == CADTypeOptions.ASYMPTOMATIC_SINGLE_VESSEL:
                dependent_risk_factor_value = weighting[VALUE][LOW_VALUE]
                dependent_efficacy_value = weighting[TREATMENT_EFFICACY][MODERATE_EFFICACY]
            elif most_recent_srs_form_response.CADType == CADTypeOptions.UNKNOWN:
                dependent_risk_factor_value = weighting[VALUE][LOW_INTERMEDIATE_VALUE]
                dependent_efficacy_value = weighting[TREATMENT_EFFICACY][MODERATE_EFFICACY]

            dependent_optimization_value = weighting[TREATMENT_OPTIM][compliance_data.cadCompliance]
            final_dependent_score *= ((dependent_risk_factor_value-1)*(1-(dependent_efficacy_value*dependent_optimization_value)))+1


        # ========================================================================
        # TODO: Make this section based on the lab values and NOT the enum values
        # ========================================================================
        # if most_recent_srs_form_response.HistoryOfHyperlipidemia:
        if most_recent_srs_form_response.LDLLevel:
            if most_recent_srs_form_response.LDLLevel == LDLLevelOptions.BORDERLINE:
                dependent_risk_factor_value = weighting[VALUE][LOW_VALUE]
                dependent_efficacy_value = weighting[TREATMENT_EFFICACY][MODERATE_EFFICACY]
            elif most_recent_srs_form_response.LDLLevel == LDLLevelOptions.HIGH:
                dependent_risk_factor_value = weighting[VALUE][LOW_INTERMEDIATE_VALUE]
                dependent_efficacy_value = weighting[TREATMENT_EFFICACY][MODERATE_EFFICACY]
            elif most_recent_srs_form_response.LDLLevel == LDLLevelOptions.VERY_HIGH:
                dependent_risk_factor_value = weighting[VALUE][LOW_INTERMEDIATE_VALUE]
                dependent_efficacy_value = weighting[TREATMENT_EFFICACY][MODERATE_EFFICACY]
            elif most_recent_srs_form_response.LDLLevel == UNKNOWN:
                dependent_risk_factor_value = weighting[VALUE][LOW_VALUE]
                dependent_efficacy_value = weighting[TREATMENT_EFFICACY][MODERATE_EFFICACY]
            # if compliance_data.ldlCompliance is not None:

            dependent_optimization_value = weighting[TREATMENT_OPTIM][compliance_data.ldlCompliance]
            final_dependent_score *= ((dependent_risk_factor_value-1)*(1-(dependent_efficacy_value*dependent_optimization_value)))+1

        if most_recent_srs_form_response.HDLLevel:
            if most_recent_srs_form_response.HDLLevel == HDLLevelOptions.LOW:
                dependent_risk_factor_value = weighting[VALUE][LOW_INTERMEDIATE_VALUE]
                dependent_efficacy_value = weighting[TREATMENT_EFFICACY][MODERATE_EFFICACY]
            elif most_recent_srs_form_response.HDLLevel == UNKNOWN:
                dependent_risk_factor_value = weighting[VALUE][LOW_VALUE]
                dependent_efficacy_value = weighting[TREATMENT_EFFICACY][MODERATE_EFFICACY]

            dependent_optimization_value = weighting[TREATMENT_OPTIM][compliance_data.hdlCompliance]
            final_dependent_score *= ((dependent_risk_factor_value-1)*(1-(dependent_efficacy_value*dependent_optimization_value)))+1

        if most_recent_srs_form_response.TriglyceridesLevel:
            if most_recent_srs_form_response.TriglyceridesLevel == TriglyceridesLevelOptions.MODERATE:
                dependent_risk_factor_value = weighting[VALUE][LOW_VALUE]
                dependent_efficacy_value = weighting[TREATMENT_EFFICACY][MODERATE_EFFICACY]
            elif most_recent_srs_form_response.TriglyceridesLevel == TriglyceridesLevelOptions.HIGH:
                dependent_risk_factor_value = weighting[VALUE][LOW_INTERMEDIATE_VALUE]
                dependent_efficacy_value = weighting[TREATMENT_EFFICACY][MODERATE_EFFICACY]
            elif most_recent_srs_form_response.TriglyceridesLevel == UNKNOWN:
                dependent_risk_factor_value = weighting[VALUE][LOW_VALUE]
                dependent_efficacy_value = weighting[TREATMENT_EFFICACY][MODERATE_EFFICACY]

            dependent_optimization_value = weighting[TREATMENT_OPTIM][compliance_data.triglyceridesCompliance]
            final_dependent_score *= ((dependent_risk_factor_value-1)*(1-(dependent_efficacy_value*dependent_optimization_value)))+1

        logger.info(f"Successfully calculated dependent risk factors...")
        return {
            "final_dependent_score": final_dependent_score,
        }

    except Exception as e:
        logger.error(f"Error calculating dependent risk factor values: {e}")
        raise e


def calculate_independent_srs_values(agg_data: dict, db_manager: SyntrilloDatabaseManager) -> tuple[float, float]:
    """
    Calculates the risk score values associated with objective metrics.
    """
    independent_risk_factor_values = get_independent_risk_factor_values(agg_data)
    independent_risk_score_total, stroke_priority_score_total = get_independent_risk_score_value(independent_risk_factor_values, db_manager)
    return independent_risk_score_total, stroke_priority_score_total


# Independent Risk Factors
def get_independent_risk_factor_values(agg_data: dict):
    """
    Calculates the risk score values associated with objective metrics.

    Returns:
        dict: The risk score values associated with objective metrics.
    """
    try:
        logger.info(f"Reformatting aggregated data into independent risk factor values...")

        tenovi_bp_data = agg_data.get('tenovi_bp_data', {})
        healthie_srs_data = agg_data.get("healthie_srs_data", {})
        lab_data = agg_data.get("lab_data", {})
        substance_use_data = agg_data.get("substance_use_data", {})

        # BP Data
        avg_trailing_sbp_value = tenovi_bp_data.get(SYSTOLIC, {}).get(TRAILING, {}).get(AVERAGE, None)
        avg_trailing_peak_sbp_value = tenovi_bp_data.get(SYSTOLIC, {}).get(TRAILING, {}).get(SBP_COUNT_175, None)
        std_trailing_sbp_value = tenovi_bp_data.get(SYSTOLIC, {}).get(TRAILING, {}).get(VARIABILITY, None)
        avg_trailing_dbp_value = tenovi_bp_data.get(DIASTOLIC, {}).get(TRAILING, {}).get(AVERAGE, None)

        # Data from Healthie
        # Fallback to baseline if there is not enough trailing data
        avg_trailing_rhr_value = healthie_srs_data["average_rhr_trailing"] if healthie_srs_data["average_rhr_trailing"] else healthie_srs_data["average_rhr_baseline"]
        avg_trailing_inactivity_value = healthie_srs_data["inactivity_hours_answer"]
        activity_minutes_answer = healthie_srs_data["activity_minutes_answer"]
        # Baseline data NOT USED-ish IN SRS CALCULATION – average_rhr_baseline_value = healthie_srs_data["average_rhr_baseline"]

        # TODO: Currently not supported due need for incorporating lab values
        creatinine_levels_value = lab_data.get("creatinine_levels", None)
        hemoglobin_value = lab_data.get("hemoglobin", None)

        # Currently not supported due to difficulty in data collection on the clinical side
        cigarette_use_value = substance_use_data.get("cigarette_use", None)
        alcohol_use_value = substance_use_data.get("alcohol_use", None)
        marijuana_use_value = substance_use_data.get("marijuana_use", None)

        #  Gender
        gender = agg_data.get("srs_response_data", [])[0].Gender.value

        logger.info(f"Successfully reformatted aggregated data into independent risk factor values...")
        return {
            GENDER: gender,
            AVG_SBP: avg_trailing_sbp_value,
            RHR: avg_trailing_rhr_value,
            HEMOGLOBIN_A1C: hemoglobin_value,
            PHYSICAL_INACTIVITY: avg_trailing_inactivity_value,
            PHYSICAL_ACTIVITY: activity_minutes_answer,
            CIGARETTE_USE: cigarette_use_value,
            ALCOHOL_USE: alcohol_use_value,
            MARIJUANA_USE: marijuana_use_value,
            SBP_STD: std_trailing_sbp_value,
            AVG_PEAK_SBP: avg_trailing_peak_sbp_value,
            AVG_DBP: avg_trailing_dbp_value,
            CREATININE: creatinine_levels_value,
        }

    except Exception as e:
        logger.error(f"Error reformatting aggregated data into independent risk factor values: {e}")
        raise e

def get_independent_risk_score_value(independent_risk_factors: dict, db_manager: SyntrilloDatabaseManager) -> tuple[float, float]:
    """
    Get the risk values for a given independent risk factors.
    """
    try:
        logger.info(f"Getting independent risk score value...")
        independent_risk_score_total = 1.0
        stroke_priority_score_total = 1.0
        for category, value in independent_risk_factors.items():
            if category in EXCLUDED_CATEGORIES:
                continue
            elif value is not None:
                if type(value) == np.float64:
                    value = float(value)
                risk_values = db_manager.get_srs_value_by_category_and_value(category, value, gender=independent_risk_factors.get(GENDER, None))
                independent_risk_score_total *= risk_values["risk_value"]
                stroke_priority_score_total *= risk_values["stroke_priority_value"]
            else:
                # Get most likely risk value for the factor
                risk_values = db_manager.get_srs_value_by_category_and_value(category, gender=independent_risk_factors.get(GENDER, None))
                independent_risk_score_total *= risk_values["risk_value"]
                stroke_priority_score_total *= risk_values["stroke_priority_value"]

        logger.info(f"Successfully got independent risk score value...")
        return independent_risk_score_total, stroke_priority_score_total

    except Exception as e:
        logger.error(f"Error getting independent risk score value: {e}")
        raise e


if __name__ == "__main__":
    # syntrillo_internal_key = uuid.UUID("6446f4da-b19a-4a1a-851e-06b5bc716160")
    syntrillo_internal_key = uuid.UUID("ff8d04c4-9307-4171-888b-447047d5fa36") # 3.33 / 5.05
    # syntrillo_internal_key = uuid.UUID("99fddf03-9304-4e48-8711-0cc4d825eb94") # 4.76 / 9.77
    srs, agg_data, stroke_priority_score = calculate_risk_score(syntrillo_internal_key)

    print("================================================")
    print(f"================ Final SRS: {srs} ===============")
    print(f"================ Final SPS: {stroke_priority_score} ===============")
    print("================================================")

        # Patient: "ff8d04c4-9307-4171-888b-447047d5fa36"
        # return {
        #     GENDER: gender,
        #     AVG_SBP: 124.21,
        #     RHR: 56.0,
        #     HEMOGLOBIN_A1C: 5.5,
        #     PHYSICAL_INACTIVITY: 8.0,
        #     PHYSICAL_ACTIVITY: activity_minutes_answer,
        #     CIGARETTE_USE: 0.0,
        #     ALCOHOL_USE: 0.0,
        #     MARIJUANA_USE: 0.0,
        #     SBP_STD: 9.30,
        #     AVG_PEAK_SBP: 133.0,
        #     AVG_DBP: 63.269,
        #     CREATININE: creatinine_levels_value,
        # }

        # Patient: "99fddf03-9304-4e48-8711-0cc4d825eb94"
        # return {
        #     GENDER: gender,
        #     AVG_SBP: 138.19,
        #     RHR: None,
        #     HEMOGLOBIN_A1C: 5.2,
        #     PHYSICAL_INACTIVITY: 5.0,
        #     PHYSICAL_ACTIVITY: activity_minutes_answer,
        #     CIGARETTE_USE: 25.0,
        #     ALCOHOL_USE: 2.0,
        #     MARIJUANA_USE: 3.0,
        #     SBP_STD: 16.90,
        #     AVG_PEAK_SBP: 161.67,
        #     AVG_DBP: 81.825,
        #     CREATININE: creatinine_levels_value,
        # }
