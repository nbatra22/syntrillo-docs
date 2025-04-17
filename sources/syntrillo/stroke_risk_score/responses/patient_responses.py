import uuid
from typing import Literal
import datetime

from syntrillo.remote_monitoring.syntrillo_database_manager import SyntrilloDatabaseManager
from syntrillo.pseudonyms_management.lookup_codes_management import LookUpCodesManagement

from syntrillo.system.logger import logger

from syntrillo.stroke_risk_score.responses.medications import MedicationParser
from syntrillo.stroke_risk_score.responses.lab_values import LabValuesResponse
from syntrillo.stroke_risk_score.responses.history import HistoryResponse
from syntrillo.stroke_risk_score.responses.test_orders import TestsOrdersResponse

class PatientResponses:
    """

    Handles retrieving necessary data points for risk score and formatting of responses.

    "response_ids" is a static variable containing all staging + production form/module ids, separated by:
        1. section
        2. subsection
        3. staging + prod
        4. metric / value
        5. form_id + module_id

    query_response() takes in form_id + module_id and returns the raw response.

    Remaining class methods are subsection-oriented. Each obtain form_id + module_id from response_ids, run query_response(), and returns formatted dict.

    """
    syntrillo_internal_key: uuid.UUID = None
    syntrillo_database_manager: SyntrilloDatabaseManager = None
    env: Literal['staging', 'prod'] = 'staging'

    response_label = {
            'section_i': {
                'medication': ['meds_statin_plavix_aspirin_anticoagulants'],
                'lab_values': ['ldl', 'halc'],
                'history': ['current_smoker', 'afib???', 'cpap_prescribed', 'cpap_regular_usage']
            },
            'section_ii': {
                'tests': ['30_day_cardiac_monitoring'],
                'history': []
            },
            'section_iii': {
                'hypertension': []
            },
            'section_iv': {
                'exercise_ids': ['vigorous', 'moderate']
            },
            'section_v': {
                'bmi': []
            },
            'section_vi': {
                'heart_rate': []
            },
            'section_vii': {
                'resting_heart_rate': []
            },
            'section_vii': {
                'smoking': []
            },
        }


    def __init__(self, syntrillo_internal_key : uuid.UUID, env) -> None:
        self.syntrillo_internal_key = syntrillo_internal_key
        self.syntrillo_database_manager = SyntrilloDatabaseManager(syntrillo_internal_key)
        self.env = env


    def query_response(self, module_label):
        '''
        Accepts form_id and module_id and returns unformatted data
        '''
        try:
            db_connection = self.syntrillo_database_manager.conn

            print(f"Patient Internal Key: {self.syntrillo_internal_key}")

            with db_connection.cursor() as cursor:
                # Get form_id and module_id using module_label
                ids_query = f"""
                    SELECT
                        form_id_{self.env},
                        module_id_{self.env}
                    FROM
                        module_label_look_up
                    WHERE
                        module_label = '{module_label}';
                """

                cursor.execute(ids_query)
                result = cursor.fetchall()

                print(f"IDS QUERY RESULT: {result} | {module_label}")

                form_id = result[0][0]
                module_id = result[0][1]

                # Get response using form_id and module_id
                response_query = f"""
                    SELECT
                        answer,
                        created_at
                    FROM
                        healthie_form_responses
                    WHERE
                        form_id = {form_id}
                        AND module_id = {module_id}
                        AND syntrillo_internal_key = '{self.syntrillo_internal_key}';
                """

                cursor.execute(response_query)
                result = cursor.fetchall()

            print(f"** 1 ** RAW RESPONSE: {result}")
            print(f"** 2 ** RESPONSE: {result[0][0]}")
            print(f"** 3 ** RESPONSE TYPE: {type(result[0][1])}")
            # print(f"***** INDEXED RESPONSE: {result[0][0]}")

            # db_connection.close()

            return result[0]

        except Exception as e:
            # logger.info(f"Error fetching form #{form_id} and module #{module_id}: {e}")
            logger.info(f"Error fetching module {module_label}: {e}")
            return None


    def close_db_conn(self):
        db_conn = self.syntrillo_database_manager.conn
        db_conn.close()


    @staticmethod
    def format_datetime(dt: datetime.datetime) -> str:
        return dt.strftime('%m/%d/%y')


    def get_etiology(self):
        response = self.query_response("stroke_etiology")

        if not response or len(response) < 2:
            return {
                'value': None,
                'date': None
            }

        etiology = response[0] or None
        date = response[1] or None

        return {
            'value': etiology,
            'date': self.format_datetime(date)
        }



    def get_medications(self):
        '''
        - Obtain form_id and module_id from response_id
        - Query raw data
        - Retrieve formatted dict via MedicationsResponse class
        '''

        (medications, med_date) = self.query_response("meds_statin_plavix_aspirin_anticoagulants")
        (compliance, comp_date) = self.query_response("medication_adherence_combined")

        db_conn = self.syntrillo_database_manager.conn

        parser = MedicationParser(prescription_str=medications, adherence_html=compliance, db_conn=db_conn)
        # meds = parser.get_medications()
        grouped_meds = parser.get_grouped_medications()

        # return meds
        return {
            'value': grouped_meds,
            'date': self.format_datetime(med_date)
        }


    def get_lab_values(self):
        '''
        - Obtain form_id and module_id from response_id
        - Query raw data
        - Retrieve formatted dict via LabValuesResponse class
        '''

        (raw_ldl_response, ldl_date) = self.query_response("ldl")

        (raw_ha1c_response, ha1c_date) = self.query_response("ha1c")

        lab_values_response = LabValuesResponse(ldl_response=raw_ldl_response, ha1c_response=raw_ha1c_response).get_lab_values()

        return {
            'value': lab_values_response,
            'date': self.format_datetime(ldl_date)
        }

    def get_history(self):
        """
        - Obtain form_id and module_id from response_id
        - Query raw data
        - Retrieve formatted dict via LabValuesResponse class
        """
        (history_raw_response, history_date) = self.query_response("medical_history") # afib, carotid stenosis, diabetes, sleep apnea

        (intra_athero_raw_response, ia_date) = self.query_response("intracranial_atherosclerosis")

        # afib_raw_response = self.query_response("null")

        # osa_raw_response = self.query_response(osa_form_id, osa_module_id)

        (smoker_raw_response, smoker_date) = self.query_response("current_smoker")

        (smoking_freq_raw_response, smoking_freq_date) = self.query_response("cigarettes_per_day_avg")

        (cpap_prescription_raw_response, cpap_pre_date) = self.query_response("cpap_prescribed")

        (cpap_usage_raw_response, cpap_use_date) = self.query_response("cpap_regular_usage")

        history_response = HistoryResponse(
            history_response=history_raw_response,
            ia_response=intra_athero_raw_response,
            # osa_response=osa_raw_response,
            smoker_response=smoker_raw_response,
            smoking_freq_response=smoking_freq_raw_response,
            cpap_prescription_response=cpap_prescription_raw_response,
            cpap_usage_response=cpap_usage_raw_response
        ).get_history()

        return {
            'value': history_response,
            'ia_date': self.format_datetime(ia_date),
            'history_date': self.format_datetime(history_date)
        }

    def get_tests_orders(self):

        (cta_performed, cta_perf_date) = self.query_response("cta_performed")
        (cardiac_monitoring_30day, cm30day_date) = self.query_response("cardiac_monitoring_30day")
        # cardiac_imaging = self.query_response("cardiac_imaging") # NEEDS STAGING MODULE
        (ha1c_6mo, ha1c6mo_date) = self.query_response("ha1c_6mo")

        tests_orders = TestsOrdersResponse(cta_performed, cardiac_monitoring_30day, ha1c_6mo).get_tests_orders()

        return {
            'value': tests_orders,
            'date': self.format_datetime(date)
        }

    def get_blood_pressure(self):
        sbp_initial = self.query_response("systolic_bp_initial")
        dbp_initial = self.query_response("diastolic_bp_initial")

        (sbp, sbp_date) = int(sbp_initial) if sbp_initial is not None else None
        (dbp, dbp_date) = int(dbp_initial) if dbp_initial is not None else None

        return {
            'value': {
                'sbp': sbp,
                'dbp': dbp
            },
            'date': self.format_datetime(sbp_date)
        }

    def get_exercise(self):
        (moderate_exercise, mod_date) = self.query_response("moderate_exercise")
        (vigorous_exercise, vig_date) = self.query_response("vigorous_exercise")

        return {
            'value': {
                'mod_exercise': moderate_exercise,
                'vig_exercise': vigorous_exercise
            },
            'date': self.format_datetime(mod_date)
        }

    def get_bmi(self):
        (height_response, height_date) = self.query_response("height_combined")
        (weight_response, weight_date) = self.query_response("weight")

        try:
            height = int(height_response)
            weight = int(weight_response)

            bmi = weight / (height ** 2) * 703

            return {
                'value': {
                    'bmi': round(bmi, 1),
                    'height': height,
                    'weight': weight
                },
                'date': self.format_datetime(height_date)
            }

        except (TypeError, ValueError):
            # Return None for BMI if inputs are invalid or missing
            return {
                'value': {
                    'bmi': None,
                    'height': height,
                    'weight': weight
                },
                'date': None
            }

    def get_hrv(self):
        return {
            "hrv": "No module available."
        }

    def get_resting_hr(self):
        (heart_rate, hr_date) = self.query_response("resting_hr_initial")

        return {
            'resting_hr': heart_rate,
            'date': self.format_datetime(hr_date)
        }

    def get_smoking(self):
        data = self.query_response("cigarettes_per_day_avg")

        return {
            'packs_per_day': data,
        }

if __name__ == "__main__":

    # healthie_user_id = "1525423" # Patient AWS Test
    healthie_user_id = "2315391" # Bob Barker

    look_up_codes_management = LookUpCodesManagement()
    entry = look_up_codes_management.retrieve_entry_by_healthie_user_id(healthie_user_id)
    internal_key = entry['syntrillo_internal_key']

    responses = PatientResponses(internal_key, env='staging')

    # etiology = responses.get_etiology()

    # medications = PatientResponses(internal_key, env='staging').get_medications()
    medications = responses.get_medications()
    print(f"***** Medication Response: {medications}")

    # lab_values = PatientResponses("99fddf03-9304-4e48-8711-0cc4d825eb94", env='staging').get_lab_values()
    # lab_values = PatientResponses(internal_key, env='staging').get_lab_values()
    # print(f"***** Lab Value Response: {lab_values}")

    # history = PatientResponses(internal_key, env='staging').get_history()
    # print(f"***** History Response: {history}")

    # tests = PatientResponses(internal_key, env='staging').get_tests_orders()
    # print(f"***** Tests/Orders Response: {tests}")

    # blood_pressure = PatientResponses(internal_key, env='staging').get_blood_pressure()
    # print(f"Blood Pressure: {blood_pressure}")

    # exercise = responses.get_exercise()
    # print(f"Blood Pressure: {exercise}")

    # bmi = PatientResponses(internal_key, env='staging').get_bmi()
    # print(f"BMI: {bmi}")

    # resting_hr = responses.get_resting_hr()
    # print(f"Resting Heart Rate: {resting_hr}")

    # smoking_freq = responses.get_smoking()
    # print(f"Smoking Frequency: {smoking_freq}")

    responses.close_db_conn()
