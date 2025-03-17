import uuid
from typing import Literal

from syntrillo.remote_monitoring.syntrillo_database_manager import SyntrilloDatabaseManager

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

    def __init__(self, syntrillo_internal_key : uuid.UUID, env) -> None:
        self.syntrillo_internal_key = syntrillo_internal_key
        self.syntrillo_database_manager = SyntrilloDatabaseManager(syntrillo_internal_key)
        self.env = env


    def get_query_response(self, form_id, module_id):
        '''
        Accepts form_id and module_id and returns unformatted data
        '''
        try:
            db_connection = self.syntrillo_database_manager.conn

            with db_connection.cursor() as cursor:
                # query = f"""
                #     SELECT
                #         t.{form_id},
                #         t.form_name,
                #         t.{module_id},
                #         t.module_label,
                #         r.syntrillo_internal_key,
                #         r.answer
                #     FROM
                #         healthie_form_templates as t
                #         JOIN healthie_form_responses as r
                #             ON t.form_id = r.form_id AND t.module_id = r.module_id
                #     WHERE
                #         r.syntrillo_internal_key = '{self.syntrillo_internal_key}';
                # """
                query = f"""
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

                cursor.execute(query)
                result = cursor.fetchall()

            print(f"***** RAW RESPONSE: {result}")
            print(f"***** RESPONSE: {type(result[0][0])}")
            print(f"***** INDEXED RESPONSE: {result[0][0]}")

            db_connection.close()

            return result[0][0]

        except Exception as e:
            logger.info(f"Error fetching form #{form_id} and module #{module_id}: {e}")
            return None

    def get_etiology(self):
        return 'Cardioembolic'

    def get_medications(self):
        '''
        - Obtain form_id and module_id from response_id
        - Query raw data
        - Retrieve formatted dict via MedicationsResponse class
        '''

        form_id = self.response_ids['section_i']["medication_ids"][self.env]['medications']["form_id"]
        module_id = self.response_ids['section_i']["medication_ids"][self.env]['medications']["module_id"]

        raw_response = self.get_query_response(form_id, module_id)

        medication_response = MedicationsResponse(medication_reponse=raw_response).prescriptions_and_compliances()

        return medication_response


    def get_lab_values(self):
        '''
        - Obtain form_id and module_id from response_id
        - Query raw data
        - Retrieve formatted dict via LabValuesResponse class
        '''

        ldl_form_id = self.response_ids['section_i']["lab_values_ids"][self.env]['ldl']["form_id"]
        ldl_module_id = self.response_ids['section_i']["lab_values_ids"][self.env]['ldl']["module_id"]
        raw_ldl_response = self.get_query_response(ldl_form_id, ldl_module_id)

        ha1c_form_id = self.response_ids['section_i']["lab_values_ids"][self.env]['ha1c']["form_id"]
        ha1c_module_id = self.response_ids['section_i']["lab_values_ids"][self.env]['ha1c']["module_id"]
        raw_ha1c_response = self.get_query_response(ha1c_form_id, ha1c_module_id)

        lab_values_response = LabValuesResponse(ldl_response=raw_ldl_response, ha1c_response=raw_ha1c_response).get_lab_values()

        return lab_values_response

    def get_history(self):
        """
        - Obtain form_id and module_id from response_id
        - Query raw data
        - Retrieve formatted dict via LabValuesResponse class
        """

        smoker_form_id = self.response_ids['section_i']["history_ids"][self.env]['smoker']["form_id"]
        smoker_module_id = self.response_ids['section_i']["history_ids"][self.env]['smoker']["module_id"]
        smoker_raw_response = self.get_query_response(smoker_form_id, smoker_module_id)

        # ia_form_id = self.response_ids['section_i']["history_ids"][self.env]['ia']["form_id"]
        # ia_module_id = self.response_ids['section_i']["history_ids"][self.env]['ia']["module_id"]
        # ia_raw_response = self.get_query_response(ia_form_id, ia_module_id)

        afib_form_id = self.response_ids['section_i']["history_ids"][self.env]['afib']["form_id"]
        afib_module_id = self.response_ids['section_i']["history_ids"][self.env]['afib']["module_id"]
        afib_raw_response = self.get_query_response(afib_form_id, afib_module_id)

        # osa_form_id = self.response_ids['section_i']["history_ids"][self.env]['osa']["form_id"]
        # osa_module_id = self.response_ids['section_i']["history_ids"][self.env]['osa']["module_id"]
        # osa_raw_response = self.get_query_response(osa_form_id, osa_module_id)

        cpap_prescription_form_id = self.response_ids['section_i']["history_ids"][self.env]['cpap_prescription']["form_id"]
        cpap_prescription_module_id = self.response_ids['section_i']["history_ids"][self.env]['cpap_prescription']["module_id"]
        cpap_prescription_raw_response = self.get_query_response(cpap_prescription_form_id, cpap_prescription_module_id)

        cpap_usage_form_id = self.response_ids['section_i']["history_ids"][self.env]['cpap_usage']["form_id"]
        cpap_usage_module_id = self.response_ids['section_i']["history_ids"][self.env]['cpap_usage']["module_id"]
        cpap_usage_raw_response = self.get_query_response(cpap_usage_form_id, cpap_usage_module_id)

        history_response = HistoryResponse(
            smoker_response=smoker_raw_response,
            # ia_response=ia_raw_response,
            afib_response=afib_raw_response,
            # osa_response=osa_raw_response,
            cpap_prescription_response=cpap_prescription_raw_response,
            cpap_usage_response=cpap_usage_raw_response
        ).get_history()

        return history_response


if __name__ == "__main__":

    medications = PatientResponses("99fddf03-9304-4e48-8711-0cc4d825eb94", env='staging').get_medications()
    print(f"***** Medication Response: {medications}")

    lab_values = PatientResponses("99fddf03-9304-4e48-8711-0cc4d825eb94", env='staging').get_lab_values()
    print(f"***** Lab Value Response: {lab_values}")

    history = PatientResponses("99fddf03-9304-4e48-8711-0cc4d825eb94", env='staging').get_history()
    print(f"***** History Response: {history}")
