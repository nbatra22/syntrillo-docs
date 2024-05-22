# ./Syntrillo_Clinic/sources/syntrillo/healthie/app_set-up.py

import os
import sys
import json

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))
sys.path.append(os.path.dirname(SCRIPT_DIR + '/../'))

from healthie.base import HealthieAPI

from data.structures.data_structure import DataStructure
from data.structures.storage_manager import StorageManager

class HealthieAPIAppSetup(HealthieAPI):
    """
    A class extending HealthieAPI to handle setting-up operations.

    """


    # list forms that can be built from data structures
    # to be used in provider sidebar iframe

