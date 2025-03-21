from datetime import datetime

from syntrillo.remote_monitoring.syntrillo_database_manager import SyntrilloDatabaseManager
from syntrillo.pseudonyms_management.lookup_codes_management import LookUpCodesManagement
from syntrillo.system.logger import logger


class HistoryResponse:

    def __init__(
            self,
            smoker_response,
            # ia_response,
            # afib_response,
            # osa_response,
            cpap_prescription_response,
            cpap_usage_response
        ):
        self.smoker_response = smoker_response
        # self.ia_response = ia_response
        # self.afib_response = afib_response
        # self.osa_response = osa_response
        self.cpap_prescription_response = cpap_prescription_response
        self.cpap_usage_response = cpap_usage_response

    def get_history(self):
        """

        Returns an object below

        {
            'smoker': boolean,
            # 'ICAD': boolean,
            'AFib': boolean,
            'OSA': boolean,
            'CPAP prescription': boolean,
            'CPAP Use': boolean
        }

        """

        return {
            'smoker': self.smoker_response,
            # 'ICAD': self.,
            # 'AFib': self.afib_response,
            # 'OSA': self.osa_response,
            'CPAP prescription': self.cpap_prescription_response,
            'CPAP Use': self.cpap_usage_response
        }


if __name__ == "__main__":
    syntrillo_database_manager = SyntrilloDatabaseManager("3261f346-ef09-4311-8a5f-f36d5d67e58d")
    db_connection = syntrillo_database_manager.conn
    # lab_values = get_history(db_connection)
    # print(f"Lab Values: {lab_values}")
