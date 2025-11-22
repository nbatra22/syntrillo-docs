import datetime
from syntrillo.medications.models import MedicationRecord, DosingScheduleRule, Frequency
from syntrillo.system.logger import logger
from syntrillo.remote_monitoring.syntrillo_medications_db_manager import SyntrilloMedicationsDatabaseQueries

def medication_from_dosing_schedule_rule(medication: MedicationRecord) -> MedicationRecord:
    """
    Fills in medication fields from a dosing schedule rule supplied byt the Frontend.

    Args:
        medication (MedicationRecord): The medication to fill in.
    Returns:
        medication (MedicationRecord): The medication with the fields filled in.
    """
    if medication.dosing_schedule_rule == DosingScheduleRule.QD:
        medication.frequency = Frequency.DAILY
        medication.dosing_interval = 1
    elif medication.dosing_schedule_rule == DosingScheduleRule.BID:
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


def sync_healthie_medications(
    syntrillo_internal_key: str,
    healthie_medications: list[dict],
    syntrillo_medication_ids: set[int]
) -> dict:
    """
    Syncs Healthie medications to Syntrillo medications.
    """
    result_log = {"medications_added": 0, "medication_logs": {}}

    # fast path: compute IDs to add, preserve original order when inserting
    existing_ids = set(syntrillo_medication_ids)  # ensure it's a set
    incoming_ids = {int(h.get("id")) for h in healthie_medications if h.get("id") is not None}
    ids_to_add = incoming_ids - existing_ids

    # if nothing to add, return early
    if not ids_to_add:
        return result_log

    # keep original order for the items we will add
    to_add = [h for h in healthie_medications if h.get("id") and int(h.get("id")) in ids_to_add]

    # create manager once
    medications_manager = SyntrilloMedicationsDatabaseQueries()

    for healthie_medication in to_add:
        hid = int(healthie_medication["id"])
        logger.info(f"Adding Healthie medication {hid} to Syntrillo for patient {syntrillo_internal_key}")
        logger.info(f"Healthie medication data: {healthie_medication}")
        logger.info(f"is_active type: {type(healthie_medication.get('is_active'))}, value: {healthie_medication.get('is_active')}")

        dosage_split = healthie_medication.get('dosage')
        if dosage_split:
            parts = dosage_split.split(' ')
        else:
            parts = [None, None]

        try:
            dosage_amount = float(parts[0]) if parts[0] is not None else None
        except (ValueError, TypeError):
            logger.error(f"Invalid dosage '{dosage_split}' for healthie_medication {hid}")
            dosage_amount = None

        dosage_unit = parts[1] if len(parts) > 1 else None

        # use datetime.datetime.fromisoformat because module imported as datetime
        start_date = None
        end_date = None
        try:
            sd = healthie_medication.get('start_date')
            ed = healthie_medication.get('end_date')

            def _parse_datetime_string(s: str):
                if not s:
                    return None
                # common formats we expect:
                # "2025-09-24 12:35:05 -0400"
                # "2025-09-24 12:35:05"
                # "2025-09-24" (date only)
                for fmt in ("%Y-%m-%d %H:%M:%S %z", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
                    try:
                        dt = datetime.datetime.strptime(s, fmt)
                        return dt
                    except Exception:
                        continue
                # final fallback: try fromisoformat for other ISO-ish strings
                try:
                    return datetime.datetime.fromisoformat(s)
                except Exception:
                    return None

            parsed_sd = _parse_datetime_string(sd) if sd else None
            parsed_ed = _parse_datetime_string(ed) if ed else None

            if parsed_sd:
                start_date = parsed_sd.date()
            if parsed_ed:
                end_date = parsed_ed.date()

        except Exception:
            logger.error(f"Could not parse dates for healthie_medication {hid}")


        medication_record = MedicationRecord(
            syntrillo_internal_key=str(syntrillo_internal_key),
            healthie_medication_id=int(hid),
            medication_name=healthie_medication.get('name'),
            is_active=healthie_medication.get('active'),
            start_date=start_date,
            end_date=end_date,
            comment=healthie_medication.get('comment'),
            directions=healthie_medication.get('directions'),
            dosage_option_id=healthie_medication.get('dosage_option_id'),
            mirrored=healthie_medication.get('mirrored'),
            dosage_amount=dosage_amount,
            dosage_unit=dosage_unit,
        )

        db_response, db_log = medications_manager.insert_patient_medication(medication_record)

        if not db_log.get('success'):
            logger.error("Failed to insert medication record for Healthie medication %s for patient %s: %s",
                         hid, syntrillo_internal_key, db_log.get('error'))
            result_log['medication_logs'][hid] = f"Failed to add Healthie medication {hid}: {db_log.get('error')}"
        else:
            result_log['medications_added'] += 1
            result_log['medication_logs'][hid] = f"Added Healthie medication {hid} to Syntrillo for patient {syntrillo_internal_key}"

    return result_log
