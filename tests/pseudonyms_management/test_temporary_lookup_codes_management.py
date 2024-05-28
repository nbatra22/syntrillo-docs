import unittest
import uuid
import re
from unittest.mock import patch, MagicMock
from syntrillo.pseudonyms_management.temporary_lookup_codes_management import TemporaryLookUpCodesManagement

class TestTemporaryLookUpCodesManagement(unittest.TestCase):

    @patch('syntrillo.pseudonyms_management.temporary_lookup_codes_management.create_connection')
    @patch('syntrillo.pseudonyms_management.temporary_lookup_codes_management.add_log_entry')
    def setUp(self, mock_add_log_entry, mock_create_connection):
        # Mock the database connection and cursor
        self.mock_conn = MagicMock()
        self.mock_cursor = MagicMock()
        mock_create_connection.return_value = (self.mock_conn, None)
        self.mock_conn.cursor.return_value = self.mock_cursor

        # Initialize the TemporaryLookUpCodesManagement instance
        self.manager = TemporaryLookUpCodesManagement(verbose=True)

    def test_generate_uuid_code(self):
        uuid_code = self.manager.generate_uuid_code()
        self.assertEqual(len(uuid_code), 36)
        self.assertTrue(isinstance(uuid_code, str))

    def test_generate_word_code(self):
        word_code = self.manager.generate_word_code()
        words = re.findall(r'[A-Z][a-z]*', word_code)
        self.assertEqual(len(words), 2)
        self.assertTrue(all(word[0].isupper() for word in words))

    def test_create_temporary_code_iframe(self):
        syntrillo_internal_key = str(uuid.uuid4())
        temp_code = self.manager.create_temporary_code(syntrillo_internal_key, 'iFrame')

        self.mock_cursor.execute.assert_called()
        self.mock_conn.commit.assert_called()
        self.assertEqual(len(temp_code), 36)
        self.assertTrue(isinstance(temp_code, str))

    def test_create_temporary_code_tenovi(self):
        syntrillo_internal_key = str(uuid.uuid4())
        temp_code = self.manager.create_temporary_code(syntrillo_internal_key, 'Tenovi')
        words = re.findall(r'[A-Z][a-z]*', temp_code)
        self.mock_cursor.execute.assert_called()
        self.mock_conn.commit.assert_called()
        self.assertEqual(len(words), 2)
        self.assertTrue(all(word[0].isupper() for word in words))



    def tearDown(self):
        self.manager.__del__()

if __name__ == '__main__':
    unittest.main()