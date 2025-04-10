from datetime import datetime
import re
from typing import Optional

from syntrillo.remote_monitoring.syntrillo_database_manager import SyntrilloDatabaseManager
from syntrillo.pseudonyms_management.lookup_codes_management import LookUpCodesManagement
from syntrillo.system.logger import logger


class HistoryResponse:

    def __init__(
            self,
            history_response,
            ia_response,
            # afib_response,
            # osa_response,
            smoker_response,
            smoking_freq_response,
            cpap_prescription_response,
            cpap_usage_response
        ):
        self.history_response = history_response
        self.ia_response = ia_response
        # self.afib_response = afib_response
        # self.osa_response = osa_response
        self.smoker_response = smoker_response
        self.smoking_freq_response = smoking_freq_response
        self.cpap_prescription_response = cpap_prescription_response
        self.cpap_usage_response = cpap_usage_response

        self.history = {
            'carotid_stenosis': None,
            'afib': None,
            'diabetes': None,
            'sleep_apnea': None,
            # 'icad': None,
            'intracranial_atherosclerosis': None,
            'smoker': None,
            'smoking_frequency': 0,
            'cpap_prescription': None,
            'cpap_use': None
        }

        self._parse_history()

    def _parse_history(self):
        # Set history answers
        if self.history_response is not None:
            conditions = self.history_response.split('|')

            for condition in conditions:

                if 'carotid stenosis' in condition.lower():
                    self.history['carotid_stenosis'] = True
                else:
                    self.history['carotid_stenosis'] = False

                if 'atrial fibrillation' in condition.lower():
                    self.history['afib'] = True
                else:
                    self.history['afib'] = False

                if 'diabetes' in condition.lower():
                    self.history['diabetes'] = True
                else:
                    self.history['diabetes'] = False

                if 'sleep apnea' in condition.lower():
                    self.history['sleep_apnea'] = True
                else:
                    self.history['sleep_apnea'] = False

        # Set intracranial atherosclerosis
        if self.ia_response == 'Yes':
            self.history['intracranial_atherosclerosis'] = True
        elif self.ia_response == 'No':
            self.history['intracranial_atherosclerosis'] = False

        # Set smoker
        if self.smoker_response == 'Yes':
            self.history['smoker'] = True
        elif self.smoker_response == 'No':
            self.history['smoker'] = False

        # Set smoking frequency
        if self.smoking_freq_response:
            self.history['smoking_frequency'] = self._extract_cigarettes_per_day(self.smoking_freq_response)
        else:
            self.history['smoking_frequency'] = None

        # Set CPAP prescription
        if self.cpap_prescription_response == 'Yes':
            self.history['cpap_prescription'] = True
        elif self.cpap_prescription_response == 'No':
            self.history['cpap_prescription'] = False

        # Set CPAP usage
        if self.cpap_usage_response == 'Yes':
            self.history['cpap_usage'] = True
        elif self.cpap_usage_response == 'No':
            self.history['cpap_usage'] = False

    def _extract_cigarettes_per_day(self, text: str) -> Optional[int]:

        # Try to extract number range from (X-Y cigarettes)
        range_match = re.search(r'\((\d+)[\s\-to]+(\d+)\s+cigarettes?\)', text, re.IGNORECASE)
        if range_match:
            low = int(range_match.group(1))
            high = int(range_match.group(2))
            return round((low + high) / 2)

        # Keyword-based estimation
        lower_text = text.lower()
        if "less than half a pack" in lower_text:
            return 5
        elif "half a pack" in lower_text and "a pack" in lower_text:
            return 15
        elif "half a pack" in lower_text:
            return 10
        elif "a pack" in lower_text or "one pack" in lower_text:
            return 20
        elif "more than a pack" in lower_text or "over a pack" in lower_text:
            return 30

        # Fallback: extract a single number of cigarettes
        single_match = re.search(r'(\d+)\s+cigarettes?', text, re.IGNORECASE)
        if single_match:
            return int(single_match.group(1))

        return None


    def get_history(self):
        return self.history


if __name__ == "__main__":
    syntrillo_database_manager = SyntrilloDatabaseManager("3261f346-ef09-4311-8a5f-f36d5d67e58d")
    db_connection = syntrillo_database_manager.conn
    # lab_values = get_history(db_connection)
    # print(f"Lab Values: {lab_values}")
