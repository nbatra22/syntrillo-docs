from syntrillo.stroke_risk_score.olivier.risk_score_olivier import StrokeRiskScore
from syntrillo.remote_monitoring.syntrillo_database_manager import SyntrilloDatabaseManager
from unittest.mock import MagicMock, patch
from uuid import UUID
import unittest
import uuid
import unittest

class TestRiskScore(unittest.TestCase):

    def test_calculate_risk_score_1(self):
        syntrillo_internal_key = '41ce2a96-a404-497c-835e-236a0f972a9d'

        risk_score_calculator = StrokeRiskScore(syntrillo_internal_key)

        result = risk_score_calculator.calculate_risk_score()[0]

        self.assertEqual(6.3, result)

if __name__ == '__main__':
    unittest.main()
