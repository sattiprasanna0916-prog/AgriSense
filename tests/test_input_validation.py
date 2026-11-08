
"""
tests/test_input_validation.py
-------------------------------
Unit tests for CropInputValidator and the Three-Level Reliability Policy.
"""

import unittest
from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split

from input_validation import CropInputValidator, FEATURES


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATASET_PATH = PROJECT_ROOT / "data" / "raw" / "Crop_recommendation.csv"


class TestCropInputValidator(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        df = pd.read_csv(DATASET_PATH)

        # Use the same training split as main.py and train_model.py.
        X_train, _, _, _ = train_test_split(
            df[FEATURES],
            df["label"],
            test_size=0.2,
            random_state=42,
            stratify=df["label"],
        )

        cls.validator = CropInputValidator(X_train)

    def test_in_distribution_sample_level_1(self):
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
        self.assertEqual(res["warnings"], [])

    def test_outside_observed_range_level_2(self):
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
            any(
                "rainfall" in warning.lower()
                and "outside the observed dataset range" in warning.lower()
                for warning in res["warnings"]
            )
        )

    def test_unusual_multivariate_combination_level_2(self):
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
        self.assertEqual(
            res["distribution_status"],
            "unusual_combination",
        )
        self.assertGreater(
            res["nearest_neighbor_distance"],
            res["reference_distance_threshold"],
        )
        self.assertLessEqual(
            res["nearest_neighbor_distance"],
            res["severe_distance_threshold"],
        )

    def test_extreme_agronomic_outlier_level_3(self):
        sample = {
            "N": 90.0,
            "P": 42.0,
            "K": 43.0,
            "temperature": 20.88,
            "humidity": 82.0,
            "ph": 13.0,
            "rainfall": 100.0,
        }

        res = self.validator.validate(sample)

        self.assertEqual(
            res["reliability_level"],
            "level_3_severe_or_invalid",
        )
        self.assertTrue(res["recommendation_withheld"])
        self.assertTrue(
            any(
                "ph" in violation.lower()
                and "viable agricultural guardrails" in violation.lower()
                for violation in res["violations"]
            )
        )

    def test_physically_impossible_input_level_3(self):
        sample = {
            "N": 90.0,
            "P": 42.0,
            "K": 43.0,
            "temperature": 20.88,
            "humidity": 125.0,
            "ph": 6.5,
            "rainfall": 100.0,
        }

        res = self.validator.validate(sample)

        self.assertEqual(
            res["reliability_level"],
            "level_3_severe_or_invalid",
        )
        self.assertTrue(res["recommendation_withheld"])
        self.assertTrue(
            any(
                "humidity" in violation.lower()
                and "physical feasibility" in violation.lower()
                for violation in res["violations"]
            )
        )

    def test_severe_multivariate_distance_level_3(self):
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

        self.assertEqual(
            res["reliability_level"],
            "level_3_severe_or_invalid",
        )
        self.assertTrue(res["recommendation_withheld"])
        self.assertGreater(
            res["nearest_neighbor_distance"],
            res["severe_distance_threshold"],
        )

    def test_non_finite_input_level_3(self):
        sample = {
            "N": float("nan"),
            "P": 42.0,
            "K": 43.0,
            "temperature": 20.88,
            "humidity": 82.0,
            "ph": 6.5,
            "rainfall": 100.0,
        }

        res = self.validator.validate(sample)

        self.assertEqual(
            res["reliability_level"],
            "level_3_severe_or_invalid",
        )
        self.assertTrue(res["recommendation_withheld"])

    def test_missing_input_level_3(self):
        sample = {
            "N": 90.0,
            "P": 42.0,
            "temperature": 20.88,
            "humidity": 82.0,
            "ph": 6.5,
            "rainfall": 100.0,
        }

        res = self.validator.validate(sample)

        self.assertEqual(
            res["reliability_level"],
            "level_3_severe_or_invalid",
        )
        self.assertTrue(res["recommendation_withheld"])

    def test_backwards_compatibility_keys(self):
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
            with self.subTest(key=key):
                self.assertIn(key, res)


if __name__ == "__main__":
    unittest.main()
