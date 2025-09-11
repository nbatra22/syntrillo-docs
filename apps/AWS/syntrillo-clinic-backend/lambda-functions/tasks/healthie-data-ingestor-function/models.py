# For this to run we need to add pydantic to our virtual environment:
# If you want to use pip
# $ pip install pydantic
#
# If you want to use us (which Pau (aka The Big Guy) strongly recommends)
# $ uv add pydantic
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

# Define the data model for the Healthie form template
class FormTemplate(BaseModel):
    form_id: str
    module_id: str
    form_name: str
    module_label: str
    module_options: str

# Define the data model for the Healthie form response
class FormResponse(BaseModel):
    form_id: str
    module_id: str
    syntrillo_internal_key: str
    answer: str
    created_at: datetime
    updated_at: datetime

# Define the data model for Healthie medications
class Medication(BaseModel):
    id: str
    name: str
    active: bool
    directions: Optional[str] = None
    dosage: Optional[str] = None
    code: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    user_id: str