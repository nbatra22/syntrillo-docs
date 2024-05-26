# Path: ./sources/syntrillo/onboarding/new_patient_set-up.py

from syntrillo.api_healthie.auth import HealthieAuth

from syntrillo.data_structures.data_structure import DataStructure
from syntrillo.data_structures.storage_manager import StorageManager

class CreateNewPatient():
    """
    A class handling initiation procedures when a new patient is created at HEalthie.

    - called by some patient webhook
    - defines ids, keys, codes, pseudonyms, and relationships between them
    - defines providers : clinician, OT, AI


    """

