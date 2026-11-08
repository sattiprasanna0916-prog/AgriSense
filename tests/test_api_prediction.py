
"""
tests/test_api_prediction.py

Integration-style tests for the AgriSense FastAPI application.

Covers:
- Health endpoint
- Evaluation endpoint
- Three-level input reliability policy
- Prediction withholding
- SHAP explanation validation
- Historical analytics endpoints
"""

import unittest

from fastapi import HTTPException

import main
from main import CropInput


class TestApiPrediction(unittest.TestCase):

    # =================================================
    # TEST INPUTS
    # =================================================

    def create_reference_input(self):
        """Create a familiar crop recommendation input."""

        return CropInput(
            N=90.0,
            P=42.0,
            K=43.0,
            temperature=20.88,
            humidity=82.0,
            ph=6.5,
            rainfall=202.94,
        )

    def create_unusual_input(self):
        """Create a plausible input outside an observed feature range."""

        return CropInput(
            N=90.0,
            P=42.0,
            K=43.0,
            temperature=20.88,
            humidity=82.0,
            ph=6.5,
            rainfall=320.0,
        )

    def create_severe_input(self):
        """Create an agronomically invalid input."""

        return CropInput(
            N=90.0,
            P=42.0,
            K=43.0,
            temperature=20.88,
            humidity=82.0,
            ph=13.0,
            rainfall=202.94,
        )

    # =================================================
    # HEALTH ENDPOINT
    # =================================================

    def test_health_endpoint(self):

        res = main.health()

        self.assertEqual(res["status"], "healthy")
        self.assertEqual(
            res["model"],
            "TabPFNClassifier",
        )
        self.assertTrue(res["model_loaded"])

    # =================================================
    # EVALUATION ENDPOINT
    # =================================================

    def test_evaluation_endpoint(self):

        res = main.evaluation()

        self.assertIn("accuracy", res)
        self.assertIn("macro_precision", res)
        self.assertIn("macro_recall", res)
        self.assertIn("macro_f1", res)

        self.assertEqual(
            res["model"],
            "TabPFNClassifier",
        )

    # =================================================
    # LEVEL 1: REFERENCE INPUT
    # =================================================

    def test_predict_level_1_reference(self):
        """
        Familiar input should produce a crop recommendation
        without withholding, when classified as Level 1.
        """

        data = self.create_reference_input()

        res = main.predict(data)

        self.assertFalse(
            res["recommendation_withheld"]
        )

        self.assertEqual(
            res["reliability_level"],
            "level_1_reference",
        )

        self.assertNotEqual(
            res["predicted_crop"],
            "Recommendation Withheld",
        )

        self.assertEqual(len(res["top_3"]), 3)

        self.assertEqual(
            res["top_3"][0]["crop"],
            res["predicted_crop"],
        )

        self.assertEqual(
            res["input_validation"]["status"],
            "passed",
        )

        self.assertEqual(
            res["input_validation"]["distribution_status"],
            "within_reference",
        )

        # Verify the response contract.
        expected_keys = [
            "predicted_crop",
            "top_3",
            "input_warnings",
            "observed_training_ranges",
            "historical_comparison",
            "notice",
            "input_validation",
            "distribution_check",
            "reliability_level",
            "recommendation_withheld",
        ]

        for key in expected_keys:
            with self.subTest(response_key=key):
                self.assertIn(key, res)

        # Verify top-three response structure.
        for item in res["top_3"]:

            self.assertIn("crop", item)
            self.assertIn("probability", item)
            self.assertIn("percentage", item)

    # =================================================
    # LEVEL 2: UNUSUAL INPUT
    # =================================================

    def test_predict_level_2_unusual_extrapolation(self):
        """
        Plausible input outside observed feature ranges should
        produce a warning rather than being withheld, if the
        configured validator classifies it as Level 2.
        """

        data = self.create_unusual_input()

        res = main.predict(data)

        self.assertFalse(
            res["recommendation_withheld"]
        )

        self.assertEqual(
            res["reliability_level"],
            "level_2_unusual",
        )

        self.assertEqual(len(res["top_3"]), 3)

        self.assertGreater(
            len(res["input_warnings"]),
            0,
        )

        self.assertTrue(
            any(
                "rainfall" in warning.casefold()
                and "outside the observed" in warning.casefold()
                for warning in res["input_warnings"]
            ),
            "Expected an observed-range rainfall warning.",
        )

    # =================================================
    # LEVEL 3: SEVERE INPUT
    # =================================================

    def test_predict_level_3_severe_outlier_withheld(self):
        """
        Agronomically invalid input must have its recommendation
        withheld and return diagnostic information.
        """

        data = self.create_severe_input()

        res = main.predict(data)

        self.assertTrue(
            res["recommendation_withheld"]
        )

        self.assertEqual(
            res["reliability_level"],
            "level_3_severe_or_invalid",
        )

        self.assertEqual(
            res["predicted_crop"],
            "Recommendation Withheld",
        )

        self.assertEqual(
            res["top_3"],
            [],
        )

        self.assertTrue(
            res["input_validation"]["recommendation_withheld"]
        )

        self.assertIn(
            "Recommendation withheld",
            res["notice"],
        )

        self.assertTrue(
            any(
                "ph" in warning.casefold()
                for warning in res["input_warnings"]
            ),
            "Expected a pH validation warning.",
        )

    # =================================================
    # SHAP EXPLANATION VALIDATION
    # =================================================

    def test_explain_withheld_input_raises_http_400(self):
        """
        SHAP explanation must not be generated for inputs
        whose crop recommendation has been withheld.
        """

        data = self.create_severe_input()

        with self.assertRaises(HTTPException) as context:
            main.explain(data)

        self.assertEqual(
            context.exception.status_code,
            400,
        )

        self.assertIn(
            "recommendation was withheld",
            context.exception.detail.casefold(),
        )

    # =================================================
    # HISTORICAL ANALYTICS
    # =================================================

    def test_historical_ranking_endpoint(self):

        ranking = main.historical_ranking(
            state="Andhra Pradesh",
            district="ANANTAPUR",
            season="Kharif",
            limit=5,
        )

        self.assertIn("crops", ranking)

        self.assertEqual(
            ranking["district"],
            "ANANTAPUR",
        )

    def test_historical_trend_endpoint(self):

        trend = main.historical_trend(
            state="Andhra Pradesh",
            district="ANANTAPUR",
            crop="Groundnut",
            season="Kharif",
        )

        self.assertIn("trend", trend)

        self.assertEqual(
            trend["crop"],
            "Groundnut",
        )

    # =================================================
    # TEST SUITE
    # =================================================


if __name__ == "__main__":
    unittest.main(verbosity=2)
