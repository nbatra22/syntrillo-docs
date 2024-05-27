# Path: ./tests/pseudonyms_management/test_lookup_codes_management.py

import unittest
from syntrillo.pseudonyms_management.lookup_codes_management import LookUpCodesManagement
import uuid

class TestLookUpCodesManagement(unittest.TestCase):

    def setUp(self):
        self.manager = LookUpCodesManagement(verbose=True)
        self.healthy_user_id = 'unittest_' + str(uuid.uuid4())

    def tearDown(self):
        self.manager.close_connection()

    def test_create_entry(self):
        entry = self.manager.create_entry(self.healthy_user_id)
        self.assertIsNotNone(entry, "Failed to create entry.")
        self.assertIn('syntrillo_internal_key', entry)
        self.assertIn('pseudo_code_for_tenovi_phi_access', entry)
        self.assertTrue(uuid.UUID(entry['syntrillo_internal_key']))
        self.assertTrue(uuid.UUID(entry['pseudo_code_for_tenovi_phi_access']))

    def test_retrieve_entry_by_healthy_user_id(self):
        self.manager.create_entry(self.healthy_user_id)
        entry = self.manager.retrieve_entry_by_healthy_user_id(self.healthy_user_id)
        self.assertIsNotNone(entry, "Failed to retrieve entry by healthy_user_id.")
        self.assertIn('syntrillo_internal_key', entry)
        self.assertIn('pseudo_code_for_tenovi_phi_access', entry)
        self.assertTrue(uuid.UUID(entry['syntrillo_internal_key']))
        self.assertTrue(uuid.UUID(entry['pseudo_code_for_tenovi_phi_access']))

    def test_retrieve_entry_by_internal_key(self):
        created_entry = self.manager.create_entry(self.healthy_user_id)
        self.assertIsNotNone(created_entry, "Failed to create entry.")
        internal_key = created_entry['syntrillo_internal_key']
        entry = self.manager.retrieve_entry_by_internal_key(internal_key)
        self.assertIsNotNone(entry, "Failed to retrieve entry by internal_key.")
        self.assertIn('healthy_user_id', entry)
        self.assertIn('pseudo_code_for_tenovi_phi_access', entry)
        self.assertTrue(uuid.UUID(entry['pseudo_code_for_tenovi_phi_access']))

    def test_retrieve_entry_by_pseudo_code(self):
        created_entry = self.manager.create_entry(self.healthy_user_id)
        self.assertIsNotNone(created_entry, "Failed to create entry.")
        pseudo_code = created_entry['pseudo_code_for_tenovi_phi_access']
        entry = self.manager.retrieve_entry_by_pseudo_code(pseudo_code)
        self.assertIsNotNone(entry, "Failed to retrieve entry by pseudo_code.")
        self.assertIn('healthy_user_id', entry)
        self.assertIn('syntrillo_internal_key', entry)
        self.assertTrue(uuid.UUID(entry['syntrillo_internal_key']))

if __name__ == '__main__':
    unittest.main()
