"""
tests/test_input_validation.py
-------------------------------
Unit tests for CropInputValidator and the Three-Level Reliability Policy.
"""

import math
import unittest
import pandas as pd
from input_validation import CropInputValidator, FEATURES


class TestCropInputValidator(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.df = pd.read_csv("data/raw/Crop_recommendation.csv")
        cls.validator = CropInputValidator(cls.df)

    def test_in_distribution_sample_level_1(self):
        """Standard crop profiles must pass with Level 1 and no warnings."""
        sample = {
            "N": 90.0,
            "P": 42.0,
            "K": 43.0,
            "temperature": 20.88,
            "humidity": 82.0,
            "ph": 6.5,
            "rainfall": 202.94,
        }
        res = self.validator.validate(sample)

        self.assertEqual(res["reliability_level"], "level_1_reference")
        self.assertFalse(res["recommendation_withheld"])
        self.assertEqual(res["range_status"], "passed")
        self.assertEqual(res["distribution_status"], "within_reference")
        self.assertLessEqual(
            res["nearest_neighbor_distance"],
            res["reference_distance_threshold"],
        )
        self.assertEqual(len(res["warnings"]), 0)

    def test_outside_observed_range_univariate_level_2(self):
        """
        Inputs outside the training dataset range but within agricultural guardrails
        must be classified as Level 2 (warning issued, but recommendation NOT withheld).
        """
        # Observed rainfall max in dataset is ~298.56 mm; 320 mm is plausible for monsoon
        sample = {
            "N": 90.0,
            "P": 42.0,
            "K": 43.0,
            "temperature": 20.88,
            "humidity": 82.0,
            "ph": 6.5,
            "rainfall": 320.0,
        }
        res = self.validator.validate(sample)

        self.assertEqual(res["reliability_level"], "level_2_unusual")
        self.assertFalse(res["recommendation_withheld"])
        self.assertEqual(res["range_status"], "warning")
        self.assertTrue(
            any("rainfall" in w and "outside the observed dataset range" in w for w in res["warnings"])
        )

    def test_unusual_multivariate_combination_level_2(self):
        """
        Inputs where all features fall within their individual observed ranges,
        but form an unusual multivariate combination, must trigger Level 2 warning.
        """
        # High N (rice/cotton), High P (apple), High K (banana) combination
        sample = {
            "N": 135.0,
            "P": 140.0,
            "K": 200.0,
            "temperature": 25.0,
            "humidity": 70.0,
            "ph": 6.5,
            "rainfall": 100.0,
        }
        res = self.validator.validate(sample)

        self.assertEqual(res["reliability_level"], "level_2_unusual")
        self.assertFalse(res["recommendation_withheld"])
        self.assertEqual(res["distribution_status"], "unusual_combination")
        self.assertGreater(
            res["nearest_neighbor_distance"],
            res["reference_distance_threshold"],
        )
        self.assertLessEqual(
            res["nearest_neighbor_distance"],
            res["severe_distance_threshold"],
        )

    def test_extreme_agronomic_outlier_level_3(self):
        """
        Inputs exceeding viable agricultural guardrails (e.g. caustic pH 13.0)
        must trigger Level 3 with recommendation withheld.
        """
        sample = {
            "N": 90.0,
            "P": 42.0,
            "K": 43.0,
            "temperature": 20.88,
            "humidity": 82.0,
            "ph": 13.0,  # Caustic, hostile to plant life
            "rainfall": 100.0,
        }
        res = self.validator.validate(sample)

        self.assertEqual(res["reliability_level"], "level_3_severe_or_invalid")
        self.assertTrue(res["recommendation_withheld"])
        self.assertTrue(
            any("ph" in v and "viable agricultural guardrails" in v for v in res["violations"])
        )

    def test_physically_impossible_input_level_3(self):
        """
        Inputs violating physical laws (humidity > 100%, pH < 0) must trigger Level 3.
        """
        sample = {
            "N": 90.0,
            "P": 42.0,
            "K": 43.0,
            "temperature": 20.88,
            "humidity": 125.0,  # Physically impossible
            "ph": 6.5,
            "rainfall": 100.0,
        }
        res = self.validator.validate(sample)

        self.assertEqual(res["reliability_level"], "level_3_severe_or_invalid")
        self.assertTrue(res["recommendation_withheld"])
        self.assertTrue(
            any("humidity" in v and "physical feasibility" in v for v in res["violations"])
        )

    def test_severe_multivariate_distance_level_3(self):
        """
        Extreme multivariate combination that exceeds severe distance threshold
        must trigger Level 3 withholding.
        """
        # Extreme toxic nutrient combination
        sample = {
            "N": 340.0,
            "P": 240.0,
            "K": 340.0,
            "temperature": 50.0,
            "humidity": 10.0,
            "ph": 3.2,
            "rainfall": 900.0,
        }
        res = self.validator.validate(sample)

        self.assertEqual(res["reliability_level"], "level_3_severe_or_invalid")
        self.assertTrue(res["recommendation_withheld"])
        self.assertGreater(
            res["nearest_neighbor_distance"],
            res["severe_distance_threshold"],
        )

    def test_non_finite_or_missing_inputs_level_3(self):
        """NaN, Inf, or missing values must be rejected cleanly as Level 3."""
        nan_sample = {
            "N": float("nan"),
            "P": 42.0,
            "K": 43.0,
            "temperature": 20.88,
            "humidity": 82.0,
            "ph": 6.5,
            "rainfall": 100.0,
        }
        res = self.validator.validate(nan_sample)
        self.assertEqual(res["reliability_level"], "level_3_severe_or_invalid")
        self.assertTrue(res["recommendation_withheld"])

        missing_sample = {
            "N": 90.0,
            "P": 42.0,
            # missing K
            "temperature": 20.88,
            "humidity": 82.0,
            "ph": 6.5,
            "rainfall": 100.0,
        }
        res2 = self.validator.validate(missing_sample)
        self.assertEqual(res2["reliability_level"], "level_3_severe_or_invalid")
        self.assertTrue(res2["recommendation_withheld"])

    def test_backwards_compatibility_keys(self):
        """Ensure all original response keys expected by legacy clients exist."""
        sample = {
            "N": 90.0,
            "P": 42.0,
            "K": 43.0,
            "temperature": 20.88,
            "humidity": 82.0,
            "ph": 6.5,
            "rainfall": 100.0,
        }
        res = self.validator.validate(sample)

        expected_keys = [
            "range_status",
            "distribution_status",
            "nearest_neighbor_distance",
            "reference_distance_threshold",
            "warnings",
            "reliability_level",
            "recommendation_withheld",
            "severe_distance_threshold",
        ]
        for key in expected_keys:
            self.assertIn(key, res)


if __name__ == "__main__":
    unittest.main()
