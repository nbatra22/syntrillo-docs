import uuid

from syntrillo.remote_monitoring.syntrillo_database_manager import SyntrilloDatabaseManager
from syntrillo.api_tenovi.device_types import DeviceTypes
from syntrillo.api_tenovi.device_measurements import DeviceMeasurements

from syntrillo.stroke_risk_score.responses.patient_responses import PatientResponses


class StrokeRiskScore:
    """

    Handles patient risk score calculation

    Breakdown:
        - Each class method is a section calculation
        - Section calculations are a combination of helper functions
        - Helper functions should return a tuple (score [int], reason [string])

    """

    syntrillo_internal_key : uuid.UUID = None
    syntrillo_database_manager : SyntrilloDatabaseManager = None
    is_staging = True

    risk_score = 0

    def __init__(self, syntrillo_internal_key : uuid.UUID) -> None:

        self.syntrillo_internal_key = syntrillo_internal_key

        # Set up PHI database connection for this user
        self.syntrillo_database_manager = SyntrilloDatabaseManager(syntrillo_internal_key)


    def calculate_risk_score(self):

        si_score = self.calculate_section_i()
        sii_score = self.calculate_section_ii()
        siii_score = self.calculate_section_iii()
        siv_score = self.calculate_section_iv()
        sv_score = self.calculate_section_v()
        svi_score = self.calculate_section_vi()
        svii_score = self.calculate_section_vii()
        sviii_score = self.calculate_section_viii()

        return si_score    \
             + sii_score   \
             + siii_score  \
             + siv_score   \
             + sv_score    \
             + svi_score   \
             + svii_score  \
             + sviii_score


    def calculate_section_i(self):

        patient_responses = PatientResponses(self.syntrillo_internal_key, env='staging')

        etiology = patient_responses.get_etiology()
        medications = patient_responses.get_medications()
        lab_values = patient_responses.get_lab_values()
        history = patient_responses.get_history()

        data = {
            'etiology': etiology,
            **medications,
            **lab_values,
            **history
        }

        score = 0

        if etiology == 'Cardioembolic':
            if medications['blood thinner'][0] == True:
                score += 6.3
            if medications['statin'][0] == True and lab_values['ldl'][0] == True:
                score += 2.6
            if medications['blood thinner'][0] == False and medications['aspirin'][0] == False and medications['plavix'][0] == False and medications['statin'][0] == False and medications['antiplate'][0] == False and medications['hypoglycemic'][0] == False and medications['antihypertensive'][0] == False and history['smoker'] == True:
                score += 1.6
            else:
                score += 6.3

        return (score, data)

    def calculate_section_ii(self):

        return

    def calculate_section_iii(self):

        return

    def calculate_section_iv(self):

        return

    def calculate_section_v(self):

        return

    def calculate_section_vi(self):

        return

    def calculate_section_vii(self):

        return

    def calculate_section_viii(self):

        return


if __name__ == "__main__":
    # risk_score = StrokeRiskScore("3261f346-ef09-4311-8a5f-f36d5d67e58d").calculate_risk_score() # no medication data

    # print(f"Patient Risk Score: {risk_score}")

    # section_1 = StrokeRiskScore("3261f346-ef09-4311-8a5f-f36d5d67e58d").calculate_section_i()
    section_1 = StrokeRiskScore("99fddf03-9304-4e48-8711-0cc4d825eb94").calculate_section_i()

    print(f"Section I data: {section_1}")


# {'blood thinner': (False, ''), 'aspirin': (True, 'chew 1 tablet by mouth daily'), 'plavix': (False, ''), 'statin': (True, 'take 1 tablet by mouth nightly'), 'antiplatte': (False, ''), 'hypoglycemic': (False, ''), 'antihypertensive': (False, ''), 'LDL': 2, 'HA1c': 0}
