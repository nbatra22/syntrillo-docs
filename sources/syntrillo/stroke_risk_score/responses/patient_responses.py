import uuid
from typing import Literal

from syntrillo.remote_monitoring.syntrillo_database_manager import SyntrilloDatabaseManager
from syntrillo.pseudonyms_management.lookup_codes_management import LookUpCodesManagement

from syntrillo.system.logger import logger

from syntrillo.stroke_risk_score.responses.section_i.medications import MedicationsResponse
from syntrillo.stroke_risk_score.responses.section_i.lab_values import LabValuesResponse
from syntrillo.stroke_risk_score.responses.section_i.history import HistoryResponse

class PatientResponses:
    """

    Handles retrieving necessary data points for risk score and formatting of responses.

    "response_ids" is a static variable containing all staging + production form/module ids, separated by:
        1. section
        2. subsection
        3. staging + prod
        4. metric / value
        5. form_id + module_id

    get_query_response() takes in form_id + module_id and returns the raw response.

    Remaining class methods are subsection-oriented. Each obtain form_id + module_id from response_ids, run get_query_response(), and returns formatted dict.

    """
    syntrillo_internal_key: uuid.UUID = None
    syntrillo_database_manager: SyntrilloDatabaseManager = None
    env: Literal['staging', 'prod'] = 'staging'

    response_ids = {
        'section_i': {
            'medication_ids': {
                'staging': {
                    'medications': {'form_id': '2155936', 'module_id': '18520987' }
                },
                'prod': {}
            },
            'lab_values_ids': {
                'staging': {
                    'ldl': {'form_id': '1765843', 'module_id': '15159782'},
                    'ha1c': {'form_id': '1765843', 'module_id': '15159786'}
                },
                'prod': {}
            },
            'history_ids': {
                'staging': {
                    'smoker': {'form_id': '2155936', 'module_id': '18519144'},
                    # 'ia': {'form_id': '1765843', 'module_id': '15159786'}, # ??
                    'afib': {'form_id': '2155936', 'module_id': '18518428'},
                    # 'osa': {'form_id': '2155936', 'module_id': '18518428'}, # ??
                    'cpap_prescription': {'form_id': '2155936', 'module_id': '18519138'},
                    'cpap_usage': {'form_id': '2155936', 'module_id': '18519139'},
                },
                'prod': {}
            }
        },
        'section_ii': {
            'tests_ids': {
                'staging': {
                    # 'cta_performed': {'form_id': '', 'module_id': ''},
                    '30_day_cardiac_monitoring': {'form_id': '2155936', 'module_id': '18518423'},
                    # 'carotid_imaging': {'form_id': '', 'module_id': ''},
                    # 'last_hemoglobin_a1c': {'form_id': '', 'module_id': ''},
                },
                'prod': {
                    # 'cta_performed': {'form_id': '2290157', 'module_id': '30011905'},
                    # '30_day_cardiac_monitoring': {'form_id': '2131055', 'module_id': '28020687'},
                    # 'carotid_imaging': {'form_id': '', 'module_id': ''},
                    # 'last_hemoglobin_a1c': {'form_id': '', 'module_id': ''},
                }
            },
            'history_ids': {
                'staging': {},
                'prod': {}
            }
        },
        'section_iii': {
            'hypertension_ids': {
                'staging': {},
                'prod': {}
            }
        },
        'section_iv': {
            'exercise_ids': {
                'staging': {
                    'vigorous': {'form_id': '2155903', 'module_id': '18516167'},
                    'moderate': {'form_id': '2155903', 'module_id': '18516168'},
                },
                'prod': {
                    'vigorous': {'form_id': '2174066', 'module_id': '29945718'},
                    'moderate': {'form_id': '2174066', 'module_id': '29945729'},
                }
            }
        },
        'section_v': {
            'bmi': {
                'staging': {},
                'prod': {}
            }
        },
        'section_vi': {
            'heart_rate': {
                'staging': {},
                'prod': {}
            }
        },
        'section_vii': {
            'resting_heart_rate': {
                'staging': {},
                'prod': {}
            }
        },
        'section_vii': {
            'smoking': {
                'staging': {},
                'prod': {}
            }
        },
    }

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


    def get_query_response(self, module_label):
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

                print(f"IDS QUERY RESULT: {result}")

                form_id = result[0][0]
                module_id = result[0][1]

                # Get response using form_id and module_id
                response_query = f"""
                    SELECT
                        answer,
                        syntrillo_internal_key
                    FROM
                        healthie_form_responses
                    WHERE
                        form_id = {form_id}
                        AND module_id = {module_id}
                        AND syntrillo_internal_key = '{self.syntrillo_internal_key}';
                """

                cursor.execute(response_query)
                result = cursor.fetchall()

            print(f"***** RAW RESPONSE: {result}")
            print(f"***** RESPONSE: {type(result[0][0])}")
            print(f"***** INDEXED RESPONSE: {result[0][0]}")

            db_connection.close()

            return result[0][0]

        except Exception as e:
            # logger.info(f"Error fetching form #{form_id} and module #{module_id}: {e}")
            logger.info(f"Error fetching form {module_label}: {e}")
            return None

    def get_etiology(self):
        return 'Cardioembolic'

    def get_medications(self):
        '''
        - Obtain form_id and module_id from response_id
        - Query raw data
        - Retrieve formatted dict via MedicationsResponse class
        '''

        raw_medication_response = self.get_query_response("meds_statin_plavix_aspirin_anticoagulants")
        raw_medication_compliance_response = self.get_query_response("medication_adherence_combined")

        medication_response = MedicationsResponse(
            medication_response=raw_medication_response,
            medication_compliance_response=raw_medication_compliance_response
            ).prescriptions_and_compliances()

        return medication_response


    def get_lab_values(self):
        '''
        - Obtain form_id and module_id from response_id
        - Query raw data
        - Retrieve formatted dict via LabValuesResponse class
        '''

        raw_ldl_response = self.get_query_response("ldl")

        raw_ha1c_response = self.get_query_response("ha1c")

        lab_values_response = LabValuesResponse(ldl_response=raw_ldl_response, ha1c_response=raw_ha1c_response).get_lab_values()

        return lab_values_response

    def get_history(self):
        """
        - Obtain form_id and module_id from response_id
        - Query raw data
        - Retrieve formatted dict via LabValuesResponse class
        """
        smoker_raw_response = self.get_query_response("current_smoker")

        # ia_raw_response = self.get_query_response("null")

        # afib_raw_response = self.get_query_response("null")

        # osa_raw_response = self.get_query_response(osa_form_id, osa_module_id)

        cpap_prescription_raw_response = self.get_query_response("cpap_prescribed")

        cpap_usage_raw_response = self.get_query_response("cpap_regular_usage")

        history_response = HistoryResponse(
            smoker_response=smoker_raw_response,
            # ia_response=ia_raw_response,
            # afib_response=afib_raw_response,
            # osa_response=osa_raw_response,
            cpap_prescription_response=cpap_prescription_raw_response,
            cpap_usage_response=cpap_usage_raw_response
        ).get_history()

        return history_response


if __name__ == "__main__":

    # healthie_user_id = "1525423"

    # look_up_codes_management = LookUpCodesManagement()
    # entry = look_up_codes_management.retrieve_entry_by_healthie_user_id(healthie_user_id)
    # internal_key = entry['syntrillo_internal_key']

    # medications = PatientResponses(internal_key, env='staging').get_medications()
    medications = PatientResponses("99fddf03-9304-4e48-8711-0cc4d825eb94", env='staging').get_medications()
    print(f"***** Medication Response: {medications}")

    # lab_values = PatientResponses("99fddf03-9304-4e48-8711-0cc4d825eb94", env='staging').get_lab_values()
    # print(f"***** Lab Value Response: {lab_values}")

    # history = PatientResponses("99fddf03-9304-4e48-8711-0cc4d825eb94", env='staging').get_history()
    # print(f"***** History Response: {history}")
