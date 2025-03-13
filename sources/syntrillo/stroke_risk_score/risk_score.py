import uuid

from syntrillo.remote_monitoring.syntrillo_database_manager import SyntrilloDatabaseManager
from syntrillo.api_tenovi.device_types import DeviceTypes
from syntrillo.api_tenovi.device_measurements import DeviceMeasurements

from syntrillo.stroke_risk_score.queries.section_i.medications import get_medications

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

        return


    def calculate_section_i(self):

        db_connection = self.syntrillo_database_manager.conn

        medications = get_medications(db_connection)

        return medications

    def calculate_section_ii(self):

        return

    def calculate_section_iii(self):

        return

    def calculate_section_iv(self):

        return

    def calculate_section_v(self):

        return

    def calculate_section_vi(self):

        return

    def calculate_section_vii(self):

        return

    def calculate_section_viii(self):

        return


if __name__ == "__main__":
    # risk_score = StrokeRiskScore("3261f346-ef09-4311-8a5f-f36d5d67e58d").calculate_risk_score()

    # print(f"Patient Risk Score: {risk_score}")

    medications = StrokeRiskScore("3261f346-ef09-4311-8a5f-f36d5d67e58d").calculate_section_i()

    print(f"Medications: {medications}")
