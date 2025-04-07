from datetime import datetime

from syntrillo.remote_monitoring.syntrillo_database_manager import SyntrilloDatabaseManager
from syntrillo.pseudonyms_management.lookup_codes_management import LookUpCodesManagement
from syntrillo.system.logger import logger

class LabValuesResponse:
    """

    *** NOT USED - RESPONSE ARE ANS

    """

    def __init__(self, ldl_response, ha1c_response):
        self.ldl_response = ldl_response
        self.ha1c_response = ha1c_response


    def get_lab_values(self):
        """

        Returns an object below

        {
            'LDL': (boolean, value)
            'HA1c': (boolean, value)
        }

        """

        if self.ldl_response is not None:
            ldl_value = (int(self.ldl_response) > 71, int(self.ldl_response))
        else:
            ldl_value = (False, None)

        if self.ha1c_response is not None:
            ha1c_value = (int(self.ha1c_response) > 71, int(self.ha1c_response))
        else:
            ha1c_value = (False, None)

        return {
            'ldl': ldl_value,
            'ha1c': ha1c_value
        }


if __name__ == "__main__":


    print(f"Lab Values: ")
