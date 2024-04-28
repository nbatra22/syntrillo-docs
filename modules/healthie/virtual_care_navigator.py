# modules/healthy/forms.py

import os
import sys
import json

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

from healthie.utils import HealthieAPIUtils

class HealthieAPIVirtualCareNavigator(HealthieAPIUtils):
    """
    A class extending HealthieAPIUtils to handle virtual care navigator operations.
    """

    def __init__(
        self,
        api_key: str = None,
        organization: str = 'staging',
        dotenv_path: str = None,
    ):
        super().__init__(api_key, organization, dotenv_path)

