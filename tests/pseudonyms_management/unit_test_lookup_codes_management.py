# Path: ./tests/pseudonyms_management/unit_test_lookup_codes_management.py
# Path: ./tests/pseudonyms_management/test_lookup_codes_management.py
import unittest
import random
from datetime import datetime
import pymysql
from syntrillo.pseudonyms_management.lookup_codes_management import LookUpCodesManagement

class TestLookUpCodesManagement(unittest.TestCase):

    def setUp(self):
        """Set up the test environment"""
        self.lookup_manager = LookUpCodesManagement(verbose=True)

    def tearDown(self):
        """Tear down the test environment"""
        try:
            self.lookup_manager.close_connection()
        except pymysql.OperationalError as e:
            print(f"OperationalError during connection close: {e}")
        except Exception as e:
            print(f"Unexpected error during connection close: {e}")

    def test_create_and_retrieve_entry(self):
        """Test the create_entry and retrieve_entry_by_healthie_user_id methods"""
        # Generate a dummy healthie_user_id
        random_number = random.randint(1000, 9999)
        date_stamp = datetime.now().strftime("%Y%m%d%H%M%S")
        healthie_user_id = f"unittest_{random_number}_{date_stamp}"

        # Test create_entry method
        create_result = self.lookup_manager.create_entry(healthie_user_id)
        self.assertIsNotNone(create_result, "Failed to create entry")
        self.assertIn('syntrillo_internal_key', create_result, "syntrillo_internal_key not in create result")
        self.assertIn('pseudo_code_for_tenovi_phi_access', create_result, "pseudo_code_for_tenovi_phi_access not in create result")

        # Test retrieve_entry_by_healthie_user_id method
        retrieve_result = self.lookup_manager.retrieve_entry_by_healthie_user_id(healthie_user_id)
        self.assertIsNotNone(retrieve_result, "Failed to retrieve entry")
        self.assertEqual(create_result['syntrillo_internal_key'], retrieve_result['syntrillo_internal_key'], "syntrillo_internal_key does not match")
        self.assertEqual(create_result['pseudo_code_for_tenovi_phi_access'], retrieve_result['pseudo_code_for_tenovi_phi_access'], "pseudo_code_for_tenovi_phi_access does not match")

if __name__ == "__main__":
    unittest.main()
