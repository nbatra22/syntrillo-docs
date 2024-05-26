# Path: ./sources/syntrillo/onboarding/new_patient_set-up.py

from syntrillo.api_healthie.auth import HealthieAuth

from syntrillo.data_structures.data_structure import DataStructure
from syntrillo.data_structures.storage_manager import StorageManager

class HealthieNewPatientSetup():
    """
    A class handling initiation procedures when a new patient is included.

    - called by some new patient webhook
    - defines providers : clinician, OT, AI


    """



