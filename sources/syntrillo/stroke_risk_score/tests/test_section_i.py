from syntrillo.stroke_risk_score.risk_score import StrokeRiskScore
from syntrillo.remote_monitoring.syntrillo_database_manager import SyntrilloDatabaseManager
from unittest.mock import MagicMock, patch
from uuid import UUID
import unittest
import uuid
import unittest

class TestSectionI(unittest.TestCase):

    def test_calculate_section_i_a(self):
        syntrillo_internal_key = '99fddf03-9304-4e48-8711-0cc4d825eb94'

        risk_score_calculator = StrokeRiskScore(syntrillo_internal_key)

        result = risk_score_calculator.calculate_section_i()

        print(f"RESULT: {result}")

        score = result[0]

        self.assertEqual(6.3, score)

if __name__ == '__main__':
    unittest.main()
