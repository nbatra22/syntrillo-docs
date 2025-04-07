from datetime import datetime

from syntrillo.remote_monitoring.syntrillo_database_manager import SyntrilloDatabaseManager
from syntrillo.pseudonyms_management.lookup_codes_management import LookUpCodesManagement
from syntrillo.system.logger import logger


class HistoryResponse:

    def __init__(
            self,
            history_response,
            # ia_response,
            # afib_response,
            # osa_response,
            smoker_response,
            cpap_prescription_response,
            cpap_usage_response
        ):
        self.history_response = history_response
        self.smoker_response = smoker_response
        # self.ia_response = ia_response
        # self.afib_response = afib_response
        # self.osa_response = osa_response
        self.cpap_prescription_response = cpap_prescription_response
        self.cpap_usage_response = cpap_usage_response

        self.history = {
            'carotid_stenosis': False,
            'afib': False,
            'diabetes': False,
            'sleep_apnea': False,
            # 'icad': False,
            # 'osa': False,
            'smoker': False,
            'cpap_prescription': False,
            'cpap_use': False
        }

        self._parse_history()

    def _parse_history(self):
        # Set history answers
        conditions = self.history_response.split('|')

        for condition in conditions:

            if 'carotid stenosis' in condition.lower():
                self.history['carotid_stenosis'] = True

            if 'atrial fibrillation' in condition.lower():
                self.history['afib'] = True

            if 'diabetes' in condition.lower():
                self.history['diabetes'] = True

            if 'sleep apnea' in condition.lower():
                self.history['sleep_apnea'] = True

        # Set smoker
        if self.smoker_response == 'Yes':
            self.history['smoker'] = True

        # Set CPAP prescription
        if self.cpap_prescription_response == 'Yes':
            self.history['cpap_prescription'] = True

        # Set smoker
        if self.cpap_usage_response == 'Yes':
            self.history['cpap_usage'] = True

    def get_history(self):
        return self.history


if __name__ == "__main__":
    syntrillo_database_manager = SyntrilloDatabaseManager("3261f346-ef09-4311-8a5f-f36d5d67e58d")
    db_connection = syntrillo_database_manager.conn
    # lab_values = get_history(db_connection)
    # print(f"Lab Values: {lab_values}")
