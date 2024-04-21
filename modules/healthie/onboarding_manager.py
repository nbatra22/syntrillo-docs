import os
import sys
import json

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

from healthie.base import HealthieAPI

class HealthieAPIOnboardingManager(HealthieAPI):
    """
    A class extending HealthieAPI to handle onboarding operations.
    """


