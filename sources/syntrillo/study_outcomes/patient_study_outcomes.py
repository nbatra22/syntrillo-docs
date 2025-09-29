from syntrillo.bp_analysis.bp_analysis import BloodPressureAnalysis
from syntrillo.remote_monitoring.syntrillo_database_manager import SyntrilloDatabaseManager
from syntrillo.pseudonyms_management.lookup_codes_management import LookUpCodesManagement
import uuid

class PatientStudyOutcomes:

    syntrillo_internal_key: uuid.UUID = None
    syntrillo_database_manager: SyntrilloDatabaseManager = None

    def __init__(self, syntrillo_internal_key):
        self.syntrillo_internal_key = syntrillo_internal_key

    def get_study_outcomes(self):
        bp_analysis_manager = BloodPressureAnalysis(self.syntrillo_internal_key)
        bp_df, _ = bp_analysis_manager.get_blood_pressure_dataframe(start_date=None, end_date=None)

        return self.syntrillo_internal_key


if __name__ == "__main__":
    healthie_user_id = '1051529'

    lookup_codes = LookUpCodesManagement()
    entry = lookup_codes.retrieve_entry_by_healthie_user_id(healthie_user_id)
    syntrillo_internal_key = entry['syntrillo_internal_key']

    patient_study_outcomes = PatientStudyOutcomes(syntrillo_internal_key=syntrillo_internal_key)
    print(patient_study_outcomes.get_study_outcomes())
