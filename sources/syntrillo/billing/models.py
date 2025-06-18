# For this to run we need to add pydantic to our virtual environment:
# If you want to use pip
# $ pip install pydantic
#
# If you want to use us (which Pau (aka The Big Guy) strongly recommends)
# $ uv add pydantic
from pydantic import BaseModel

# Define the model for a single claim to be inserted in the billing_records table
class Claim(BaseModel):
    service_line_id: str
    claim_id: str
    encounter_id: str
    claim_status: str
    syntrillo_internal_key: str
    cpt_code: str = None
    date_of_service_start: str
    date_of_service_end: str = None

class BillingEligibility(BaseModel):
    syntrillo_internal_key: str
    cpt_code: str
    bp_device_training_status: bool
    eligible_to_bill: bool