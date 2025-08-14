import uuid
import numpy as np

from syntrillo.remote_monitoring.syntrillo_database_manager import SyntrilloDatabaseManager
from syntrillo.stroke_risk_score_v2.agg_data import aggregate_data
from syntrillo.stroke_risk_score_v2.constants import (
    LOW_VALUE,
    LOW_INTERMEDIATE_VALUE,
    INTERMEDIATE_HIGH_VALUE,
    HIGH_VALUE,
    MODERATE_EFFICACY,
    HIGH_EFFICACY,
    TREATMENT_OPTIMIZATION,
    TREATMENT_PARTIALLY_OPTIMIZED,
    TREATMENT_NOT_OPTIMIZED,
    AVG_SBP,
    RHR,
    HEMOGLOBIN_A1C,
    PHYSICAL_INACTIVITY,
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
        TREATMENT_OPTIMIZATION: 1.0,
        TREATMENT_PARTIALLY_OPTIMIZED: 0.5,
        TREATMENT_NOT_OPTIMIZED: 0.0,
    }
}


def calculate_risk_score(syntrillo_internal_key: uuid.UUID):
    """
    Calculate the risk score for a given syntrillo internal key
    """
    agg_data = aggregate_data(syntrillo_internal_key)
    db_manager = SyntrilloDatabaseManager(syntrillo_internal_key)

    independent_risk_factor_values = calculate_independent_srs_values(agg_data, db_manager)
    dependent_risk_factor_values = calculate_dependent_risk_factors(agg_data)

    dependent_risk_factor_values = dependent_risk_factor_values["dependent_risk_factor_values"]
    dependent_efficacy_values = dependent_risk_factor_values["dependent_efficacy_values"]
    dependent_optimization_values = dependent_risk_factor_values["dependent_optimization_values"]

    total_risk_factor_score = dependent_risk_factor_values + independent_risk_factor_values
    raw_total_srs = ((total_risk_factor_score-1)*(1-(dependent_efficacy_values*dependent_optimization_values)))+1 # TODO: Currently not supported due to lack of information from Clinical team.
    final_srs = round(raw_total_srs**0.70, 2)

    return final_srs



def calculate_dependent_risk_factors(agg_data: dict) -> dict:
    """
    Calculates the risk score values associated with dependent risk factors.

    Args:
        agg_data (dict): The aggregated data
    Returns:
        dict: The risk score values associated with dependent risk factors.
    """
    most_recent_srs_form_response: SRSFormResponse = agg_data.get("srs_response_data", None)

    # treatment_compliance = most_recent_srs_form_response.compliance

    dependent_risk_factor_values = 0.
    dependent_efficacy_values = 0.
    dependent_optimization_values = 0. # TODO: Currently not supported due to lack of information from Clinical team.
    # Link to Google sheet of treatment optimization: https://docs.google.com/spreadsheets/d/1d9lE8EbwfIhnkV9028yV2ccXM17noWHxLXscdBYc_ZA/edit?gid=1878192176#gid=1878192176

    # History of ischemia
    # Code is not optimized becuase the values might change in the future.
    if most_recent_srs_form_response.HasPreviousStroke:
        if most_recent_srs_form_response.NumberOfStrokes == NumberOfStrokesOptions.ONE:
            if most_recent_srs_form_response.LatestStrokeMechanism == StrokeMechanismOptions.SMALL_VESSEL:
                dependent_risk_factor_values += weighting[VALUE][HIGH_VALUE]
                dependent_efficacy_values += weighting[TREATMENT_EFFICACY][HIGH_EFFICACY]
            elif most_recent_srs_form_response.LatestStrokeMechanism == StrokeMechanismOptions.LARGE_VESSEL:
                dependent_risk_factor_values += weighting[VALUE][HIGH_VALUE]
                dependent_efficacy_values += weighting[TREATMENT_EFFICACY][HIGH_EFFICACY]
            elif most_recent_srs_form_response.LatestStrokeMechanism == StrokeMechanismOptions.CARDIOEMBOLIC:
                dependent_risk_factor_values += weighting[VALUE][HIGH_VALUE]
                dependent_efficacy_values += weighting[TREATMENT_EFFICACY][HIGH_EFFICACY]
            elif most_recent_srs_form_response.LatestStrokeMechanism == StrokeMechanismOptions.CRYPTOGENIC:
                dependent_risk_factor_values += weighting[VALUE][HIGH_VALUE]
                dependent_efficacy_values += weighting[TREATMENT_EFFICACY][HIGH_EFFICACY]
            elif most_recent_srs_form_response.LatestStrokeMechanism == StrokeMechanismOptions.HYPERCOAGULABLE:
                dependent_risk_factor_values += weighting[VALUE][HIGH_VALUE]
                dependent_efficacy_values += weighting[TREATMENT_EFFICACY][HIGH_EFFICACY]
            elif most_recent_srs_form_response.LatestStrokeMechanism == StrokeMechanismOptions.STRUCTURAL:
                dependent_risk_factor_values += weighting[VALUE][HIGH_VALUE]
                dependent_efficacy_values += weighting[TREATMENT_EFFICACY][HIGH_EFFICACY]

        elif most_recent_srs_form_response.NumberOfStrokes == NumberOfStrokesOptions.MULTIPLE:
            if most_recent_srs_form_response.LatestStrokeMechanism == StrokeMechanismOptions.SMALL_VESSEL:
                dependent_risk_factor_values += weighting[VALUE][HIGH_VALUE]
                dependent_efficacy_values += weighting[TREATMENT_EFFICACY][HIGH_EFFICACY]
            elif most_recent_srs_form_response.LatestStrokeMechanism == StrokeMechanismOptions.LARGE_VESSEL:
                dependent_risk_factor_values += weighting[VALUE][HIGH_VALUE]
                dependent_efficacy_values += weighting[TREATMENT_EFFICACY][HIGH_EFFICACY]
            elif most_recent_srs_form_response.LatestStrokeMechanism == StrokeMechanismOptions.CRYPTOGENIC:
                dependent_risk_factor_values += weighting[VALUE][HIGH_VALUE]
                dependent_efficacy_values += weighting[TREATMENT_EFFICACY][HIGH_EFFICACY]
            elif most_recent_srs_form_response.LatestStrokeMechanism == StrokeMechanismOptions.HYPERCOAGULABLE:
                dependent_risk_factor_values += weighting[VALUE][HIGH_VALUE]
                dependent_efficacy_values += weighting[TREATMENT_EFFICACY][HIGH_EFFICACY]
            elif most_recent_srs_form_response.LatestStrokeMechanism == StrokeMechanismOptions.STRUCTURAL:
                dependent_risk_factor_values += weighting[VALUE][HIGH_VALUE]
                dependent_efficacy_values += weighting[TREATMENT_EFFICACY][MODERATE_EFFICACY]

    if most_recent_srs_form_response.ScreenedForTIA and most_recent_srs_form_response.LikelihoodOfTIA == LikelihoodOfTIAOptions.HIGH_LIKELIHOOD:
        if most_recent_srs_form_response.TIAMechanism == StrokeMechanismOptions.SMALL_VESSEL:
            dependent_risk_factor_values += weighting[VALUE][HIGH_VALUE]
            dependent_efficacy_values += weighting[TREATMENT_EFFICACY][HIGH_EFFICACY]
        elif most_recent_srs_form_response.TIAMechanism == StrokeMechanismOptions.LARGE_VESSEL:
            dependent_risk_factor_values += weighting[VALUE][HIGH_VALUE]
            dependent_efficacy_values += weighting[TREATMENT_EFFICACY][HIGH_EFFICACY]
        elif most_recent_srs_form_response.TIAMechanism == StrokeMechanismOptions.CRYPTOGENIC:
            dependent_risk_factor_values += weighting[VALUE][HIGH_VALUE]
            dependent_efficacy_values += weighting[TREATMENT_EFFICACY][HIGH_EFFICACY]
        elif most_recent_srs_form_response.TIAMechanism == StrokeMechanismOptions.HYPERCOAGULABLE:
            dependent_risk_factor_values += weighting[VALUE][HIGH_VALUE]
            dependent_efficacy_values += weighting[TREATMENT_EFFICACY][HIGH_EFFICACY]
        elif most_recent_srs_form_response.TIAMechanism == StrokeMechanismOptions.CARDIOEMBOLIC:
            dependent_risk_factor_values += weighting[VALUE][HIGH_VALUE]
            dependent_efficacy_values += weighting[TREATMENT_EFFICACY][HIGH_EFFICACY]
        elif most_recent_srs_form_response.TIAMechanism == StrokeMechanismOptions.STRUCTURAL:
            dependent_risk_factor_values += weighting[VALUE][HIGH_VALUE]
            dependent_efficacy_values += weighting[TREATMENT_EFFICACY][MODERATE_EFFICACY]

    if most_recent_srs_form_response.HasPriorHeadCT and most_recent_srs_form_response.ChronicInfarctPresent:
        if most_recent_srs_form_response.ChronicInfarctMechanism == StrokeMechanismOptions.SMALL_VESSEL:
            dependent_risk_factor_values += weighting[VALUE][HIGH_VALUE]
            dependent_efficacy_values += weighting[TREATMENT_EFFICACY][HIGH_EFFICACY]
        elif most_recent_srs_form_response.ChronicInfarctMechanism == StrokeMechanismOptions.LARGE_VESSEL:
            dependent_risk_factor_values += weighting[VALUE][HIGH_VALUE]
            dependent_efficacy_values += weighting[TREATMENT_EFFICACY][HIGH_EFFICACY]
        elif most_recent_srs_form_response.ChronicInfarctMechanism == StrokeMechanismOptions.CRYPTOGENIC:
            dependent_risk_factor_values += weighting[VALUE][HIGH_VALUE]
            dependent_efficacy_values += weighting[TREATMENT_EFFICACY][HIGH_EFFICACY]
        elif most_recent_srs_form_response.ChronicInfarctMechanism == StrokeMechanismOptions.HYPERCOAGULABLE:
            dependent_risk_factor_values += weighting[VALUE][HIGH_VALUE]
            dependent_efficacy_values += weighting[TREATMENT_EFFICACY][HIGH_EFFICACY]
        elif most_recent_srs_form_response.ChronicInfarctMechanism == StrokeMechanismOptions.CARDIOEMBOLIC:
            dependent_risk_factor_values += weighting[VALUE][HIGH_VALUE]
            dependent_efficacy_values += weighting[TREATMENT_EFFICACY][HIGH_EFFICACY]
        elif most_recent_srs_form_response.ChronicInfarctMechanism == StrokeMechanismOptions.STRUCTURAL:
            dependent_risk_factor_values += weighting[VALUE][HIGH_VALUE]
            dependent_efficacy_values += weighting[TREATMENT_EFFICACY][MODERATE_EFFICACY]

    if most_recent_srs_form_response.HistoryOfAtrialFibrillation:
        dependent_risk_factor_values += weighting[VALUE][HIGH_VALUE]
        dependent_efficacy_values += weighting[TREATMENT_EFFICACY][HIGH_EFFICACY]

    if most_recent_srs_form_response.HistoryOfIronDeficiencyAnemia:
        if most_recent_srs_form_response.AnemiaSeverity == AnemiaSeverityOptions.MILD:
            dependent_risk_factor_values += weighting[VALUE][LOW_VALUE]
            dependent_efficacy_values += weighting[TREATMENT_EFFICACY][MODERATE_EFFICACY]
        elif most_recent_srs_form_response.AnemiaSeverity == AnemiaSeverityOptions.SEVERE:
            dependent_risk_factor_values += weighting[VALUE][LOW_INTERMEDIATE_VALUE]
            dependent_efficacy_values += weighting[TREATMENT_EFFICACY][MODERATE_EFFICACY]

    if most_recent_srs_form_response.HistoryOfArterialClots:
        if most_recent_srs_form_response.ArterialClotOccurrences == ArterialClotOccurrencesOptions.SINGLE_PRIOR_EVENT:
            dependent_risk_factor_values += weighting[VALUE][LOW_INTERMEDIATE_VALUE]
            dependent_efficacy_values += weighting[TREATMENT_EFFICACY][MODERATE_EFFICACY]
        elif most_recent_srs_form_response.ArterialClotOccurrences == ArterialClotOccurrencesOptions.MULTIPLE_PRIOR_EVENTS:
            dependent_risk_factor_values += weighting[VALUE][INTERMEDIATE_HIGH_VALUE]
            dependent_efficacy_values += weighting[TREATMENT_EFFICACY][MODERATE_EFFICACY]

    if most_recent_srs_form_response.HistoryOfVenousClots:
        if most_recent_srs_form_response.PFOPresence == PFOPresenceOptions.POSITIVE:
            if most_recent_srs_form_response.VenousClotOccurrences == VenousClotOccurrencesOptions.SINGLE:
                dependent_risk_factor_values += weighting[VALUE][LOW_INTERMEDIATE_VALUE]
                dependent_efficacy_values += weighting[TREATMENT_EFFICACY][MODERATE_EFFICACY]
            elif most_recent_srs_form_response.VenousClotOccurrences == VenousClotOccurrencesOptions.MULTIPLE:
                dependent_risk_factor_values += weighting[VALUE][INTERMEDIATE_HIGH_VALUE]
                dependent_efficacy_values += weighting[TREATMENT_EFFICACY][MODERATE_EFFICACY]
        elif most_recent_srs_form_response.PFOPresence == PFOPresenceOptions.UNKNOWN:
            if most_recent_srs_form_response.VenousClotOccurrences == VenousClotOccurrencesOptions.SINGLE:
                dependent_risk_factor_values += weighting[VALUE][LOW_VALUE]
                dependent_efficacy_values += weighting[TREATMENT_EFFICACY][MODERATE_EFFICACY]
            elif most_recent_srs_form_response.VenousClotOccurrences == VenousClotOccurrencesOptions.MULTIPLE:
                dependent_risk_factor_values += weighting[VALUE][LOW_VALUE]
                dependent_efficacy_values += weighting[TREATMENT_EFFICACY][MODERATE_EFFICACY]

    if most_recent_srs_form_response.LDLLevel == LDLLevelOptions.BORDERLINE:
        dependent_risk_factor_values += weighting[VALUE][LOW_VALUE]
        dependent_efficacy_values += weighting[TREATMENT_EFFICACY][MODERATE_EFFICACY]
    elif most_recent_srs_form_response.LDLLevel == LDLLevelOptions.HIGH:
        dependent_risk_factor_values += weighting[VALUE][LOW_INTERMEDIATE_VALUE]
        dependent_efficacy_values += weighting[TREATMENT_EFFICACY][MODERATE_EFFICACY]
    elif most_recent_srs_form_response.LDLLevel == LDLLevelOptions.VERY_HIGH:
        dependent_risk_factor_values += weighting[VALUE][LOW_INTERMEDIATE_VALUE]
        dependent_efficacy_values += weighting[TREATMENT_EFFICACY][MODERATE_EFFICACY]
    elif most_recent_srs_form_response.LDLLevel == LDLLevelOptions.UNKNOWN:
        dependent_risk_factor_values += weighting[VALUE][LOW_VALUE]
        dependent_efficacy_values += weighting[TREATMENT_EFFICACY][MODERATE_EFFICACY]

    if most_recent_srs_form_response.HDLLevel == HDLLevelOptions.LOW:
        dependent_risk_factor_values += weighting[VALUE][LOW_INTERMEDIATE_VALUE]
        dependent_efficacy_values += weighting[TREATMENT_EFFICACY][MODERATE_EFFICACY]
    elif most_recent_srs_form_response.HDLLevel == HDLLevelOptions.UNKNOWN:
        dependent_risk_factor_values += weighting[VALUE][LOW_VALUE]
        dependent_efficacy_values += weighting[TREATMENT_EFFICACY][MODERATE_EFFICACY]

    if most_recent_srs_form_response.TriglyceridesLevel == TriglyceridesLevelOptions.MODERATE:
        dependent_risk_factor_values += weighting[VALUE][LOW_VALUE]
        dependent_efficacy_values += weighting[TREATMENT_EFFICACY][MODERATE_EFFICACY]
    elif most_recent_srs_form_response.TriglyceridesLevel == TriglyceridesLevelOptions.HIGH:
        dependent_risk_factor_values += weighting[VALUE][LOW_INTERMEDIATE_VALUE]
        dependent_efficacy_values += weighting[TREATMENT_EFFICACY][MODERATE_EFFICACY]
    elif most_recent_srs_form_response.TriglyceridesLevel == TriglyceridesLevelOptions.UNKNOWN:
        dependent_risk_factor_values += weighting[VALUE][LOW_VALUE]
        dependent_efficacy_values += weighting[TREATMENT_EFFICACY][MODERATE_EFFICACY]

    if most_recent_srs_form_response.HistoryOfCHF:
        if most_recent_srs_form_response.EjectionFraction == EjectionFractionOptions.LESS_THAN_OR_EQUAL_40:
            dependent_risk_factor_values += weighting[VALUE][INTERMEDIATE_HIGH_VALUE]
            dependent_efficacy_values += weighting[TREATMENT_EFFICACY][MODERATE_EFFICACY]
        elif most_recent_srs_form_response.EjectionFraction == EjectionFractionOptions.GREATER_THAN_40:
            dependent_risk_factor_values += weighting[VALUE][LOW_INTERMEDIATE_VALUE]
            dependent_efficacy_values += weighting[TREATMENT_EFFICACY][MODERATE_EFFICACY]
        elif most_recent_srs_form_response.EjectionFraction == EjectionFractionOptions.UNKNOWN:
            dependent_risk_factor_values += weighting[VALUE][LOW_INTERMEDIATE_VALUE]
            dependent_efficacy_values += weighting[TREATMENT_EFFICACY][MODERATE_EFFICACY]

    if most_recent_srs_form_response.HistoryOfCarotidStenosis:
        if most_recent_srs_form_response.StenosisPercentage == StenosisPercentageOptions.FIFTY_TO_SEVENTY:
            dependent_risk_factor_values += weighting[VALUE][LOW_INTERMEDIATE_VALUE]
            dependent_efficacy_values += weighting[TREATMENT_EFFICACY][HIGH_EFFICACY]
        elif most_recent_srs_form_response.StenosisPercentage == StenosisPercentageOptions.GREATER_THAN_SEVENTY:
            dependent_risk_factor_values += weighting[VALUE][HIGH_VALUE]
            dependent_efficacy_values += weighting[TREATMENT_EFFICACY][HIGH_EFFICACY]
        elif most_recent_srs_form_response.StenosisPercentage == StenosisPercentageOptions.UNKNOWN:
            dependent_risk_factor_values += weighting[VALUE][INTERMEDIATE_HIGH_VALUE]
            dependent_efficacy_values += weighting[TREATMENT_EFFICACY][HIGH_EFFICACY]

    if most_recent_srs_form_response.HistoryOfOSA:
        if most_recent_srs_form_response.OSASeverity == OSASeverityOptions.MILD:
            dependent_risk_factor_values += weighting[VALUE][LOW_VALUE]
            dependent_efficacy_values += weighting[TREATMENT_EFFICACY][HIGH_EFFICACY]
        elif most_recent_srs_form_response.OSASeverity == OSASeverityOptions.MODERATE:
            dependent_risk_factor_values += weighting[VALUE][LOW_INTERMEDIATE_VALUE]
            dependent_efficacy_values += weighting[TREATMENT_EFFICACY][HIGH_EFFICACY]
        elif most_recent_srs_form_response.OSASeverity == OSASeverityOptions.SEVERE:
            dependent_risk_factor_values += weighting[VALUE][INTERMEDIATE_HIGH_VALUE]
            dependent_efficacy_values += weighting[TREATMENT_EFFICACY][HIGH_EFFICACY]
        elif most_recent_srs_form_response.OSASeverity == OSASeverityOptions.UNKNOWN:
            dependent_risk_factor_values += weighting[VALUE][LOW_INTERMEDIATE_VALUE]
            dependent_efficacy_values += weighting[TREATMENT_EFFICACY][HIGH_EFFICACY]

    if most_recent_srs_form_response.HistoryOfValvularHeartDisease:
        dependent_risk_factor_values += weighting[VALUE][INTERMEDIATE_HIGH_VALUE]
        dependent_efficacy_values += weighting[TREATMENT_EFFICACY][HIGH_EFFICACY]

    if most_recent_srs_form_response.HistoryOfCAD:
        if most_recent_srs_form_response.CADType == CADTypeOptions.SYMPTOMATIC_MULTI_OR_SINGLE_VESSEL:
            dependent_risk_factor_values += weighting[VALUE][INTERMEDIATE_HIGH_VALUE]
            dependent_efficacy_values += weighting[TREATMENT_EFFICACY][MODERATE_EFFICACY]
        elif most_recent_srs_form_response.CADType == CADTypeOptions.ASYMPTOMATIC_MULTIVESSEL:
            dependent_risk_factor_values += weighting[VALUE][INTERMEDIATE_HIGH_VALUE]
            dependent_efficacy_values += weighting[TREATMENT_EFFICACY][MODERATE_EFFICACY]
        elif most_recent_srs_form_response.CADType == CADTypeOptions.ASYMPTOMATIC_SINGLE_VESSEL:
            dependent_risk_factor_values += weighting[VALUE][LOW_VALUE]
            dependent_efficacy_values += weighting[TREATMENT_EFFICACY][MODERATE_EFFICACY]
        elif most_recent_srs_form_response.CADType == CADTypeOptions.UNKNOWN:
            dependent_risk_factor_values += weighting[VALUE][LOW_INTERMEDIATE_VALUE]
            dependent_efficacy_values += weighting[TREATMENT_EFFICACY][MODERATE_EFFICACY]

    return {
        "dependent_risk_factor_values": dependent_risk_factor_values,
        "dependent_efficacy_values": dependent_efficacy_values,
        "dependent_optimization_values": dependent_optimization_values,
    }



def calculate_independent_srs_values(agg_data: dict, db_manager: SyntrilloDatabaseManager) -> float:
    """
    Calculates the risk score values associated with objective metrics.
    """
    independent_risk_factor_values = get_independent_risk_factor_values(agg_data)
    independent_risk_score_total = get_independent_risk_score_value(independent_risk_factor_values, db_manager)
    return independent_risk_score_total


# Independent Risk Factors
def get_independent_risk_factor_values(agg_data: dict):
    """
    Calculates the risk score values associated with objective metrics.

    Returns:
        dict: The risk score values associated with objective metrics.
    """
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
    avg_trailing_inactivity_value = healthie_srs_data.get("inactivity_minutes_answer", None)
    # Baseline data NOT USED-ish IN SRS CALCULATION – average_rhr_baseline_value = healthie_srs_data["average_rhr_baseline"]

    # TODO: Currently not supported due need for incorporating lab values
    creatinine_levels_value = lab_data.get("creatinine_levels", None)
    hemoglobin_value = lab_data.get("hemoglobin", None)

    # Currently not supported due to difficulty in data collection on the clinical side
    cigarette_use_value = substance_use_data.get("cigarette_use", None)
    alcohol_use_value = substance_use_data.get("alcohol_use", None)
    marijuana_use_value = substance_use_data.get("marijuana_use", None)

    return {
        AVG_SBP: avg_trailing_sbp_value,
        RHR: avg_trailing_rhr_value,
        HEMOGLOBIN_A1C: hemoglobin_value,
        PHYSICAL_INACTIVITY: avg_trailing_inactivity_value,
        CIGARETTE_USE: cigarette_use_value,
        ALCOHOL_USE: alcohol_use_value,
        MARIJUANA_USE: marijuana_use_value,
        SBP_STD: std_trailing_sbp_value,
        AVG_PEAK_SBP: avg_trailing_peak_sbp_value,
        AVG_DBP: avg_trailing_dbp_value,
        CREATININE: creatinine_levels_value,
    }

def get_independent_risk_score_value(independent_risk_factors: dict, db_manager: SyntrilloDatabaseManager) -> float:
    """
    Get the risk values for a given independent risk factors.
    """
    independent_risk_score_total = 0.
    for category, value in independent_risk_factors.items():
        if value:
            if type(value) == np.float64:
                value = float(value)
            independent_risk_score_total += db_manager.get_srs_value_by_category_and_value(category, value)
        else:
            # Get most likely risk value for the factor
            independent_risk_score_total += db_manager.get_srs_value_by_category_and_value(category)

    return independent_risk_score_total


if __name__ == "__main__":
    syntrillo_internal_key = uuid.UUID("ff8d04c4-9307-4171-888b-447047d5fa36")
    srs = calculate_risk_score(syntrillo_internal_key)

    print("================================================")
    print(f"======== Final SRS: {srs} =========")
    print("================================================")