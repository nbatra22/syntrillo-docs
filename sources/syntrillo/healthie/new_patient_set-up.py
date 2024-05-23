# ./Syntrillo_Clinic/sources/syntrillo/healthie/new_patient_set-up.py

from syntrillo.healthie.auth import HealthieAuth

from data.structures.data_structure import DataStructure
from data.structures.storage_manager import StorageManager

class HealthieNewPatientSetup():
    """
    A class extending HealthieAPI to handle initiation procedures when a new patient is included.

    - called by some new patient webhook
    - defines providers : clinician, OT, AI


    """



