import uuid

from syntrillo.remote_monitoring.syntrillo_database_manager import SyntrilloDatabaseManager
from syntrillo.api_tenovi.device_types import DeviceTypes
from syntrillo.api_tenovi.device_measurements import DeviceMeasurements
from syntrillo.pseudonyms_management.lookup_codes_management import LookUpCodesManagement

from syntrillo.stroke_risk_score.responses.patient_responses import PatientResponses
from syntrillo.stroke_risk_score.score_calculator.section_i import SectionOneCalculator


class StrokeRiskScore:
    """

    Handles patient risk score calculation

    Breakdown:
        - Each class method is a section calculation
        - Section calculations are a combination of helper functions
        - Helper functions should return a tuple (score [int], reason [string])

    """

    patient_responses: PatientResponses = None
    is_staging = True

    risk_score = 0

    def __init__(self, syntrillo_internal_key : uuid.UUID) -> None:

        self.patient_responses = PatientResponses(syntrillo_internal_key=syntrillo_internal_key, env='staging')


    def calculate_risk_score(self):

        si_score, si_data = self._section_i()
        sii_score, sii_data = self._section_ii()
        siii_score, siii_data = self._section_iii()
        siv_score, siv_data = self._section_iv()
        sv_score, sv_data = self._section_v()
        # svi_score, svi_data = self._section_vi()
        svii_score, svii_data = self._section_vii()
        sviii_score, sviii_data = self._section_viii()

        total_score = si_score + sii_score + siii_score + siv_score + sv_score + svii_score + svii_score

        data = {
            'i': (si_score, si_data),
            'ii': (sii_score, sii_data),
            'iii': (siii_score, siii_data),
            'iv': (siv_score, siv_data),
            'v': (sv_score, sv_data),
            # 'vi': (svi_score, svi_data),
            'vii': (svii_score, svii_data),
            'viii': (sviii_score, sviii_data),
        }

        return {
            'total_score': total_score,
            'data': data
        }


    def _section_i(self):

        etiology = self.patient_responses.get_etiology()
        medications = self.patient_responses.get_medications()
        lab_values = self.patient_responses.get_lab_values()
        history = self.patient_responses.get_history()

        data = {
            'etiology': etiology,
            'medications': medications,
            'lab_values': lab_values,
            'history': history
        }

        score = 0

        calculator = SectionOneCalculator(data)

        if etiology == 'Cardioembolic':
            score = calculator.score_cardioembolic()

        if etiology == 'Large Vessel':
            score = calculator.score_large_vessel()

        if etiology == 'Small Vessel':
            score = calculator.score_small_vessel()

        if etiology == 'Cryptogenic':
            score = calculator.score_cryptogenic()

        if etiology == 'Other':
            score = calculator.score_other()

        if etiology == 'N/A':
            score = calculator.score_na()

        return (score, data)

    def _section_ii(self):

        data = self.patient_responses.get_tests_orders()

        score = 0

        return (score, data)

    def _section_iii(self):

        data = self.patient_responses.get_blood_pressure()

        systolic = data['sbp']
        diastolic = data['dbp']

        if systolic < 130 and diastolic < 90:
            score = 0

        if systolic > 130 and systolic < 190:
            score = (systolic - 130) / 20
        else:
            score = 3

        if diastolic > 80 and diastolic < 90:
            score = (diastolic - 80) / 3.33
        else:
            score = 3

        return (score, data)


    def _section_iv(self):

        data = self.patient_responses.get_exercise()

        mod_exercise = int(data['mod_exercise'])
        vig_exercise = int(data['vig_exercise'])

        total_min = mod_exercise + vig_exercise

        if total_min <= 0:
            score = 0.0
        elif total_min >= 200:
            score = 2.0
        else:
            score = (total_min / 200) * 2

        return (score, data)


    def _section_v(self):

        data = self.patient_responses.get_bmi()

        if data['bmi'] <= 30:
            score = 0.0
        elif data['bmi'] >= 60:
            score = 2.0
        else:
            # Linear interpolation between 30 and 60
            score = (data['bmi'] - 30) / (60 - 30) * 2

        return (score, data)


    # def _section_vi(self):

    #     return


    def _section_vii(self):

        data = self.patient_responses.get_resting_hr()

        hr = int(data['resting_hr'])

        if hr <= 60:
            score = 0.0
        elif hr >= 100:
            score = 1.0
        else:
            score = (hr - 60) / (100 - 60)

        return (score, data)


    def _section_viii(self):

        data = self.patient_responses.get_smoking()

        score = 0

        return (score, data)


if __name__ == "__main__":
    healthie_user_id = "1525423"

    look_up_codes_management = LookUpCodesManagement()
    entry = look_up_codes_management.retrieve_entry_by_healthie_user_id(healthie_user_id)
    internal_key = entry['syntrillo_internal_key']

    # risk_score = StrokeRiskScore(syntrillo_internal_key=internal_key).calculate_risk_score()
    # print(f"Risk Score: {risk_score}")

    section_i = StrokeRiskScore(syntrillo_internal_key=internal_key)._section_i()
    print(f"Section I: {section_i}")


# {'blood thinner': (False, ''), 'aspirin': (True, 'chew 1 tablet by mouth daily'), 'plavix': (False, ''), 'statin': (True, 'take 1 tablet by mouth nightly'), 'antiplatte': (False, ''), 'hypoglycemic': (False, ''), 'antihypertensive': (False, ''), 'LDL': 2, 'HA1c': 0}
