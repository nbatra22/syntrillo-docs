from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum
from decimal import Decimal
from datetime import date, timezone
from pydantic import Field

class Frequency(str, Enum):
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    ONE_TIME = "one-time"

class Condition(str, Enum):
    BID = "BID"
    TID = "TID"
    QID = "QID"
    PRN = "PRN"

class TimeOfDay(str, Enum):
    MORNING = "morning"
    AFTERNOON = "afternoon"
    EVENING = "evening"
    NIGHT = "night"
    BEDTIME = "bedtime"

class DeliveryMethod(str, Enum):
    CREAM = "cream"
    TABLET_PILL_CAPSULE = "tablet/pill/capsule"
    IMPLANT = "implant"
    INHALER = "inhaler"
    SUPPOSITORIES = "suppositories"
    INJECTION = "injection"
    OTHER = "other"


class MedicationRecord(BaseModel):
    """
    Pydantic model representing a single record in the medications_records table.
    This model validates the data type and constraints for one medication entry.
    """
    # Required Fields (NOT NULL)
    syntrillo_internal_key: str = Field(..., max_length=255)
    medication_id: int
    medication_name: str = Field(..., max_length=255)

    # Nullable Fields
    dosage_amount: Decimal | None = Field(default=None, max_digits=10, decimal_places=3)
    dosage_unit: str | None = Field(default=None, max_length=32)
    comment: str | None = None
    directions: str | None = None
    frequency: Frequency | None = None
    interval: int | None = None
    condition: Condition | None = None
    dose_count: int | None = None
    time_of_day: TimeOfDay | None = None
    start_date: date | None = None
    end_date: date | None = None
    dosage_option_id: str | None = Field(default=None, max_length=255)
    delivery_method: DeliveryMethod | None = None

    # Fields with Defaults
    is_active: bool = True

    # For a default that is dynamically generated for each instance, like a timestamp,
    # we use `default_factory`.
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

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