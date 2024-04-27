import os
import sys
import json

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))
sys.path.append(os.path.dirname(SCRIPT_DIR + '/../'))

from healthie.base import HealthieAPI

from data.structures.data_structure import DataStructure
from data.structures.storage_manager import StorageManager

class HealthieAPINewPatientSetup(HealthieAPI):
    """
    A class extending HealthieAPI to handle initiation procedures when a new patient is included.

    - called by some new patient webhook
    - defines providers : clinician, OT, AI


    """



