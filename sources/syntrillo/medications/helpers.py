from syntrillo.medications.models import MedicationRecord, DosingScheduleRule, Frequency


def medication_from_dosing_schedule_rule(medication: MedicationRecord) -> MedicationRecord:
    """
    Fills in medication fields from a dosing schedule rule supplied byt the Frontend.

    Args:
        medication (MedicationRecord): The medication to fill in.
    Returns:
        medication (MedicationRecord): The medication with the fields filled in.
    """
    if medication.dosing_schedule_rule == DosingScheduleRule.BID:
        medication.frequency = Frequency.DAILY
        medication.dosing_interval = 2
    elif medication.dosing_schedule_rule == DosingScheduleRule.TID:
        medication.frequency = Frequency.DAILY
        medication.dosing_interval = 3
    elif medication.dosing_schedule_rule == DosingScheduleRule.QID:
        medication.frequency = Frequency.DAILY
        medication.dosing_interval = 4
    elif medication.dosing_schedule_rule == DosingScheduleRule.PRN:
        medication.frequency = Frequency.ONE_TIME
        medication.dosing_interval = None
    else:
        raise Exception(f"Invalid dosing schedule rule: {medication.dosing_schedule_rule}")

    return medication