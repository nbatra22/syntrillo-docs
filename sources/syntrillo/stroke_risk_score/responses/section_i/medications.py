from datetime import datetime

from syntrillo.remote_monitoring.syntrillo_database_manager import SyntrilloDatabaseManager
from syntrillo.pseudonyms_management.lookup_codes_management import LookUpCodesManagement
from syntrillo.system.logger import logger

class MedicationsResponse:

    def __init__(self, medication_reponse):
        self.medication_reponse = medication_reponse

        self.flagged_medicines = {
            'blood thinner': (False, ""),
            "aspirin": (False, ""),
            "plavix": (False, ""),
            "statin": (False, ""),
            "antiplatte": (False, ""),
            "hypoglycemic": (False, ""),
            "antihypertensive": (False, "")
        }


    def formatted_prescriptions_and_compliances(self):
        '''
        Example of answer to split and clean:
        "Acetaminophen Extra Strength Oral Tablet\r|500 MG\r|\r|take 2 tablets by mouth\r|\r|\r|\r|\r|6920f1f6-fc56-4ebe-91da-1d83604a80ba\r|\r|Z2lkOi8vRG9zZXNwb3QvRG9zZXNwb3Q6Ok1lZGljYXRpb25TZWFyY2hSZXN1bHQvMzEzNzU\\\\Xanax Oral Tablet\r|0.5 MG\r|true\r|take 1 tablet by mouth every 9 hours\r|\r|\r|PRN\r|\r|d2ed0c78-f701-4dfe-98a1-9003e18b2501\r|\r|Z2lkOi8vRG9zZXNwb3QvRG9zZXNwb3Q6Ok1lZGljYXRpb25TZWFyY2hSZXN1bHQvMzA4ODA\\\\amLODIPine Besylate Oral Tablet\r|10 MG\r|true\r|take 1 tablet by mouth daily\r|\r|\r|\r|\r|f30a88e5-dd21-4e3f-9b73-5c2ad7d08208\r|\r|Z2lkOi8vRG9zZXNwb3QvRG9zZXNwb3Q6Ok1lZGljYXRpb25TZWFyY2hSZXN1bHQvMzU2OTQ\\\\Aspirin 81 Oral Tablet Chewable\r|81 MG\r|true\r|chew 1 tablet by mouth daily\r|Tue Oct 22 2024 00:00:00 GMT-0500 (Central Daylight Time)\r|\r|\r|\r|c1848fe5-90f2-4208-bb9b-b1cb55e69618\r|\r|Z2lkOi8vRG9zZXNwb3QvRG9zZXNwb3Q6Ok1lZGljYXRpb25TZWFyY2hSZXN1bHQvMjUxNDY\\\\Atorvastatin Calcium Oral Tablet\r|20 MG\r|true\r|take 1 tablet by mouth nightly\r|\r|\r|\r|\r|5a0d95c7-3889-4d9c-b65c-e9e5fa613863\r|\r|Z2lkOi8vRG9zZXNwb3QvRG9zZXNwb3Q6Ok1lZGljYXRpb25TZWFyY2hSZXN1bHQvMTIxNzk\\\\Clopidogrel Bisulfate Oral Tablet\r|75 MG\r|false\r|take 1 tablet. by mouth daily for 21 days\r|Tue Oct 22 2024 00:00:00 GMT-0500 (Central Daylight Time)\r|\r|\r|\r|6c37d0e8-4770-4034-936b-b7d65938dbc0\r|\r|Z2lkOi8vRG9zZXNwb3QvRG9zZXNwb3Q6Ok1lZGljYXRpb25TZWFyY2hSZXN1bHQvMjIx\\\\Escitalopram Oxalate Oral Tablet\r|5 MG\r|true\r|take 1 tablet by mouth daily\r|\r|\r|\r|\r|61a48051-a73b-43bd-83bd-3a327e026d74\r|\r|Z2lkOi8vRG9zZXNwb3QvRG9zZXNwb3Q6Ok1lZGljYXRpb25TZWFyY2hSZXN1bHQvMjQwNzA\\\\Flonase Allergy Relief Nasal Suspension\r|50 MCG/ACT\r|true\r|1 spray by nasal route daily\r|\r|\r|PRN\r|\r|c6d854eb-45eb-44bd-ae08-71f3da054ceb\r|\r|Z2lkOi8vRG9zZXNwb3QvRG9zZXNwb3Q6Ok1lZGljYXRpb25TZWFyY2hSZXN1bHQvMTIxMzY\\\\Loratadine Oral Capsule\r|10 MG\r|true\r|take 1 capsule by mouth daily\r|\r|\r|\r|\r|da52652e-ed5f-48d6-afec-e56b5d6d9f75\r|\r|Z2lkOi8vRG9zZXNwb3QvRG9zZXNwb3Q6Ok1lZGljYXRpb25TZWFyY2hSZXN1bHQvMzMwMjQ\\\\Losartan Potassium Oral Tablet\r|50 MG\r|true\r|take 1 tablet by mouth daily\r|\r|\r|\r|\r|47bb7897-6ed2-4e97-8ed9-74686bd0d5c9\r|\r|Z2lkOi8vRG9zZXNwb3QvRG9zZXNwb3Q6Ok1lZGljYXRpb25TZWFyY2hSZXN1bHQvMTY2MzQ\\\\Metoprolol Tartrate Oral Tablet\r|100 MG\r|true\r|Take 2 tablets by mouth\r|\r|\r|\r|\r|9ec644db-13cd-4447-bfda-c8f6413d5e70\r|\r|Z2lkOi8vRG9zZXNwb3QvRG9zZXNwb3Q6Ok1lZGljYXRpb25TZWFyY2hSZXN1bHQvNDY5NA\\\\PriLOSEC OTC Oral Tablet Delayed Release\r|\r|true\r|Take 1 capsule (10 mg) by mouth daily with dinner\r|\r|\r|\r|\r|e304e59f-5de2-4755-a2f6-ec977b5068ba\\\\Tadalafil Oral Tablet\r|5 MG\r|true\r|take 1 tablet by mouth daily\r|\r|\r|\r|\r|c4e02a23-f2ec-494d-aeea-075b38ceca2c\r|\r|Z2lkOi8vRG9zZXNwb3QvRG9zZXNwb3Q6Ok1lZGljYXRpb25TZWFyY2hSZXN1bHQvMzYzNjQ\\\\Ambien Oral Tablet\r|5 MG\r|\r|take 2 tablets by mouth every 24 hours\r|\r|\r|\r|\r|1da74df8-2686-454d-8571-84a8309ef6ad\r|\r|Z2lkOi8vRG9zZXNwb3QvRG9zZXNwb3Q6Ok1lZGljYXRpb25TZWFyY2hSZXN1bHQvMzYxNzY"
        '''

        # Handle empty medication_response
        if self.medication_reponse == None:
            return None

        split_medication_reponse = self.medication_reponse.split('\\\\')

        formated_prescriptions_and_compliances = [
            (
                med.split('|')[0].strip('\\\r').lower(),
                med.split('|')[3].strip('\\\r').lower()
            )
            for med in split_medication_reponse
        ]
        return formated_prescriptions_and_compliances

    def prescriptions_and_compliances(self):
        '''
        Example of output:
        {'blood thinner': (False, ''), 'aspirin': (True, 'chew 1 tablet by mouth daily'), 'plavix': (False, ''), 'statin': (True, 'take 1 tablet by mouth nightly'), 'antiplatte': (False, ''), 'hypoglycemic': (False, ''), 'antihypertensive': (False, '')}
        '''
        prescriptions_and_compliances = self.flagged_medicines

        formated_prescriptions_and_compliances = self.formatted_prescriptions_and_compliances()

        # Handle empty medication answers
        if formated_prescriptions_and_compliances == None:
            return prescriptions_and_compliances

        for flagged_medicine in self.flagged_medicines:
            for prescription, compliance in formated_prescriptions_and_compliances:
                if flagged_medicine in prescription:
                    prescriptions_and_compliances[flagged_medicine] = (True, compliance)


        return prescriptions_and_compliances

    def blood_thinner(self):
        true_or_false = 0
        return self.prescriptions_and_compliances()["blood thinner"][true_or_false]
