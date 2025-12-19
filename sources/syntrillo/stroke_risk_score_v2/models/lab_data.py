from pydantic import BaseModel
from typing import Optional

# Main data model for SRS form response
class LabData(BaseModel):
    # Required fields (NOT NULL in database)
    ldl_value: Optional[float] = None
    hdl_value: Optional[float] = None
    creatintine_value: Optional[float] = None
    hgA1c_value: Optional[float] = None
    hsCRP_value: Optional[float] = None
    hemoglobin_value: Optional[float] = None