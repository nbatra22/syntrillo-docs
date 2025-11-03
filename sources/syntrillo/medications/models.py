from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum
from decimal import Decimal
from datetime import date, timezone, time
from pydantic import Field

class Frequency(str, Enum):
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    ONE_TIME = "one-time"
    AS_NEEDED = "as-needed"

class DosingScheduleRule(str, Enum):
    BID = "BID"
    TID = "TID"
    QID = "QID"
    PRN = "PRN"

class TimeOfDay(str, Enum):
    MORNING = "morning"
    NOON = "noon"
    AFTERNOON = "afternoon"
    EVENING = "evening"
    NIGHT = "night"
    BEDTIME = "bedtime"

class DeliveryMethod(str, Enum):
    CREAM = "cream"
    PILL_TABLET_CAPSULE = "pill/tablet/capsule"
    IMPLANT = "implant"
    INHALER = "inhaler"
    SUPPOSITORIES = "suppositories"
    INJECTION = "injection"
    OTHER = "other"

class DrugCategory(str, Enum): # Mechanism of Action (MOA)
    ANTI_PLATELET = "antiplatelet"
    ANTI_HYPERTENSIVE = "antihypertensive"
    STATIN = "statin"
    HYPOLYCEMIC_AGENT = "hypoglycemic-agent"
    ACE_INHIBITOR = "ace_inhibitor"
    ARB = "arb"
    BETA_BLOCKER = "beta_blocker"
    CALCIUM_CHANNEL_BLOCKER = "calcium_channel_blocker"
    DIURETIC = "diuretic"
    OTHER = "other"

class DrugSupercategory(str, Enum):
    BLOOD_THINNER = "blood_thinner"
    CHOLESTEROL_MEDICATION = "cholesterol_medication"
    DIABETES_MEDICATION = "diabetes_medication"
    BLOOD_PRESSURE_MEDICATION = "blood_pressure_medication"
    OTHER = "other"

class MedicationRecord(BaseModel):
    """
    Pydantic model representing a single record in the medications_records table.
    This model validates the data type and constraints for one medication entry.
    """
    # Required Fields (NOT NULL)
    syntrillo_internal_key: str = Field(..., max_length=255)
    medication_name: str = Field(..., max_length=255)
    medication_id: int = 0
    is_active: bool = True
    dosage_option_id: str = Field(default=None, max_length=255) # type: ignore # default=None bc. of merge_medication_records func.

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Nullable Fields
    category: Optional[DrugCategory] = None # new
    supercategory: Optional[DrugSupercategory] = None # new
    should_track: Optional[bool] = True # new
    dosage_amount: Optional[float] = 1.0
    dosage_unit: Optional[str] = Field(default=None, max_length=32)
    comment: Optional[str] = None
    directions: Optional[str] = None
    frequency: Optional[Frequency] = None
    dosing_interval: Optional[int] = None
    dosing_schedule_rule: Optional[DosingScheduleRule] = None
    dose_count: Optional[int] = None
    time_of_day: Optional[TimeOfDay] = None
    time_of_day_specific: Optional[time] = None # new
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    delivery_method: Optional[DeliveryMethod] = None
    mirrored: Optional[bool] = False

    class Config:
        # This allows the model to be created from ORM objects (like SQLAlchemy)
        from_attributes = True


# --- Example Usage ---

# 1. Creating a valid medication record (minimal required fields)
#     med_record_valid = MedicationRecord(
#         syntrillo_internal_key=str(uuid.uuid4()),
#         medication_id=101,
#         medication_name="Lisinopril",
#         dosage_amount=Decimal("10.000"),
#         dosage_unit="mg",
#         frequency=Frequency.DAILY,
#         time_of_day=TimeOfDay.MORNING,
#         start_date=date(2025, 9, 24)
#     )
#     # The `created_at` field is automatically populated with the current UTC time.
#     print("--- Valid Record ---")
#     print(med_record_valid.model_dump_json(indent=2))
