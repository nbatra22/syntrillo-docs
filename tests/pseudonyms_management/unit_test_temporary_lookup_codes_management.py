# Path: ./tests/pseudonyms_management/unit_test_temporary_lookup_codes_management.py
# Path: ./tests/pseudonyms_management/test_temporary_lookup_codes_management.py

import unittest
import uuid
from syntrillo.pseudonyms_management.temporary_lookup_codes_management import TemporaryLookUpCodesManagement

class TestTemporaryLookUpCodesManagement(unittest.TestCase):

    def test_temporary_code_management(self):
        # Initialize TemporaryLookUpCodesManagement instance
        manager = TemporaryLookUpCodesManagement(verbose=True)

        # Generate a dummy syntrillo_internal_key
        syntrillo_internal_key = str(uuid.uuid4())

        # Create a temporary code for 'iFrame' purpose
        temp_code_iframe = manager.create_temporary_pseudo_code(syntrillo_internal_key, TemporaryLookUpCodesManagement.PURPOSE_HEALTHIE_IFRAME)
        self.assertIsNotNone(temp_code_iframe, "Failed to create temporary code for iFrame purpose")

        # Create a temporary code for 'Tenovi' purpose
        temp_code_tenovi = manager.create_temporary_pseudo_code(syntrillo_internal_key, TemporaryLookUpCodesManagement.PURPOSE_TENOVI_PAIRING)
        self.assertIsNotNone(temp_code_tenovi, "Failed to create temporary code for Tenovi purpose")

        # Retrieve syntrillo internal key using the temporary code and purpose
        retrieved_key_iframe = manager.retrieve_syntrillo_internal_key(temp_code_iframe, TemporaryLookUpCodesManagement.PURPOSE_HEALTHIE_IFRAME)
        self.assertEqual(retrieved_key_iframe, syntrillo_internal_key, "Retrieved syntrillo internal key for iFrame does not match")

        retrieved_key_tenovi = manager.retrieve_syntrillo_internal_key(temp_code_tenovi, TemporaryLookUpCodesManagement.PURPOSE_TENOVI_PAIRING)
        self.assertEqual(retrieved_key_tenovi, syntrillo_internal_key, "Retrieved syntrillo internal key for Tenovi does not match")

        # Delete an entry using the temporary code and purpose
        manager.delete_entry(temp_code_iframe, TemporaryLookUpCodesManagement.PURPOSE_HEALTHIE_IFRAME)
        retrieved_key_iframe_after_deletion = manager.retrieve_syntrillo_internal_key(temp_code_iframe, TemporaryLookUpCodesManagement.PURPOSE_HEALTHIE_IFRAME)
        self.assertIsNone(retrieved_key_iframe_after_deletion, "Failed to delete temporary code for iFrame purpose")

        # Delete old entries (older than 24 hours)
        manager.delete_old_entries()
        print("Deleted entries older than 24 hours.")

if __name__ == "__main__":
    unittest.main()
