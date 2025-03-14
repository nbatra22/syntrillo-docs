import uuid

from syntrillo.remote_monitoring.syntrillo_database_manager import SyntrilloDatabaseManager
from syntrillo.api_tenovi.device_types import DeviceTypes
from syntrillo.api_tenovi.device_measurements import DeviceMeasurements

from syntrillo.system.logger import logger

from syntrillo.stroke_risk_score.queries.section_i.medications_olivier import MedicationsResponse

class PatientResponses:
    syntrillo_internal_key : uuid.UUID = None
    syntrillo_database_manager : SyntrilloDatabaseManager = None

    def __init__(self, syntrillo_internal_key : uuid.UUID, response_ids) -> None:
        self.syntrillo_internal_key = syntrillo_internal_key
        self.syntrillo_database_manager = SyntrilloDatabaseManager(syntrillo_internal_key)

        self.patient_responses = self.form_responses()
        self.response_ids = response_ids

        self.medications = self.medications()

    def form_responses(self):
        '''
        We read all the responses for a given patient
        '''
        db_connection = self.syntrillo_database_manager.conn

        with db_connection.cursor() as cursor:
            query = f"""
                SELECT 
                    t.form_id, 
                    t.form_name, 
                    t.module_id, 
                    t.module_label, 
                    r.syntrillo_internal_key, 
                    r.answer  
                FROM 
                    healthie_form_templates as t 
                    JOIN healthie_form_responses as r 
                        ON t.form_id = r.form_id AND t.module_id = r.module_id 
                WHERE 
                    r.syntrillo_internal_key = '{self.syntrillo_internal_key}';
            """

            cursor.execute(query)
            result = cursor.fetchall()
        
        db_connection.close()

        return result

    def stroke_ethiology(self):
        return 'Cardioembolic'

    def medications(self):
        '''
        We filter a specific response among all the response 
        for a specific patient (in this case medication question)

        Then we return a dedictated object which can process the response (in this case Medications)
        '''
        medication_form_id_module_id = (
            self.response_ids["medication_response"]["form_id"], 
            self.response_ids["medication_response"]["module_id"],
        )

        patient_medication_reponses = [
            response[5] 
            for response in self.patient_responses 
            if (
                response[0] == medication_form_id_module_id[0] 
                and response[2] == medication_form_id_module_id[1]
            ) 
        ][0]

        return MedicationsResponse(patient_medication_reponses)

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

    risk_score = 0

    def __init__(self, syntrillo_internal_key : uuid.UUID) -> None:

        self.syntrillo_internal_key = syntrillo_internal_key

        # Set up PHI database connection for this user
        self.syntrillo_database_manager = SyntrilloDatabaseManager(syntrillo_internal_key)

    def calculate_risk_score(self):

        db_connection = self.syntrillo_database_manager.conn

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

        # This will be different in PROD and STAGING
        response_ids={
            'medication_response': {'form_id': '2155936', 'module_id': '18520987' }
            # ...
        }

        patient_responses = PatientResponses(self.syntrillo_internal_key, response_ids)

        if patient_responses.stroke_ethiology() == 'Cardioembolic':
            if not patient_responses.medications.blood_thinner():
                return 6.3

        return None
    
    def calculate_section_ii(self):

        return 0

    def calculate_section_iii(self):

        return 0

    def calculate_section_iv(self):

        return 0

    def calculate_section_v(self):

        return 0

    def calculate_section_vi(self):

        return 0

    def calculate_section_vii(self):

        return 0

    def calculate_section_viii(self):

        return 0
