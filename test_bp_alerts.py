#!/usr/bin/env python3
"""
Test script for blood pressure alerts
"""

import sys
import os

# Add the sources directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'sources'))

from syntrillo.bp_alerts.bp_alert_manager import BloodPressureAlertManager
from syntrillo.pseudonyms_management.lookup_codes_management import LookUpCodesManagement

def test_bp_alerts():
    """Test the blood pressure alert functionality"""

    # You'll need to provide actual test data
    test_syntrillo_internal_key = "your-test-internal-key"  # Replace with actual test key
    test_healthie_user_id = "your-test-healthie-user-id"    # Replace with actual test user ID

    try:
        # Test the alert manager
        alert_manager = BloodPressureAlertManager(test_syntrillo_internal_key, test_healthie_user_id)

        # Test the two-week alerts
        result = alert_manager.handle_two_week_alerts()
        print(f"Two-week alerts result: {result}")

    except Exception as e:
        print(f"Error testing BP alerts: {e}")

if __name__ == "__main__":
    test_bp_alerts()
