import unittest

from calculate_score import *

class TestCalculateScore(unittest.TestCase):

    def test_format_score_input_table(self):
        cleaned_patient_data = [
            {
                "form_id": 1136356,
                "form_name": "Stroke Risk Factors Input",
                "module_id": 9798955,
                "module_label": "Blood thinner - Prescribed ?",
                "syntrillo_internal_key": "3261f346-ef09-4311-8a5f-f36d5d67e58d",
                "answer": 'No'
            },      
        ]

        expected_result = {
            "syntrillo_internal_key": "3261f346-ef09-4311-8a5f-f36d5d67e58d",
            "section_1": [
                {
                    "cardioembolic_lines": [
                        { "blood_thinner": "No"},
                    ]
                },
            ]
        }

        result = format_score_input_table(cleaned_patient_data)

        self.assertEqual(result, expected_result)

    def test_calculate_score_cardioembolic_one_line_one_cell(self):
        # This is suppose to map the speadsheet
        score_input_table = {
            "syntrillo_internal_key": "3261f346-ef09-4311-8a5f-f36d5d67e58d",
            "section_1": [
                { 
                    "cardioembolic_lines": [
                        { "blood_thinner": "No"},
                    ]
                },
            ]
        }
        result = calculate_score(score_input_table)
        self.assertEqual(result, '6.3')

if __name__ == '__main__':
    unittest.main()