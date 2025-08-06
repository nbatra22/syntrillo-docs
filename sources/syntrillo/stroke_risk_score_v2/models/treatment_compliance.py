from pydantic import BaseModel
from enum import Enum

class TreatmentComplianceOptions(str, Enum):
    OPTIMIZED = "optimized"
    PARTIALLY_OPTIMIZED = "partially optimized"
    NOT_OPTIMIZED = "not optimized"


# Main data model for SRS form response
class TreatmentCompliance(BaseModel):
    # Required fields (NOT NULL in database)
    srs_form_response_id: int # Foreign key to srs_form_responses table
    strokeCompliance: TreatmentComplianceOptions
    tiaCompliance: TreatmentComplianceOptions
    chronicInfarctCompliance: TreatmentComplianceOptions
    atrialFibrillationCompliance: TreatmentComplianceOptions
    ironDeficiencyAnemiaCompliance: TreatmentComplianceOptions
    arterialClotsCompliance: TreatmentComplianceOptions
    venousClotsCompliance: TreatmentComplianceOptions
    chfCompliance: TreatmentComplianceOptions
    carotidStenosisCompliance: TreatmentComplianceOptions
    osaCompliance: TreatmentComplianceOptions
    cadCompliance: TreatmentComplianceOptions
    valvularHeartDiseaseCompliance: TreatmentComplianceOptions
    ckdCompliance: TreatmentComplianceOptions
    pfoCompliance: TreatmentComplianceOptions
