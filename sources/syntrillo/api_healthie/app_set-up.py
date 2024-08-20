# Path: ./sources/syntrillo/api_healthie/app_set-up.py


from syntrillo.api_healthie.auth import HealthieAuth

from syntrillo.data_structures.data_structure import DataStructure
from syntrillo.data_structures.storage_manager_local_file_system import StorageManager

class HealthieAppSetup():
    """
    A class extending HealthieAPI to handle setting-up operations.

    """


    # list forms that can be built from data structures
    # to be used in provider sidebar iframe

