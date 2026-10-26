"""
tests/test_api_prediction.py
-----------------------------
Integration tests for FastAPI application endpoints in main.py,
validating the three-level reliability policy, response contracts,
and prediction withholding behavior.
"""

import unittest
from fastapi import HTTPException
import main
from main import CropInput


class TestApiPrediction(unittest.TestCase):
    def test_health_endpoint(self):
        """Health endpoint must return status and model information."""
        res = main.health()
        self.assertEqual(res["status"], "healthy")
        self.assertEqual(res["model"], "TabPFNClassifier")
        self.assertTrue(res["model_loaded"])

    def test_evaluation_endpoint(self):
        """Evaluation endpoint must return recorded model metrics."""
        res = main.evaluation()
        self.assertIn("accuracy", res)
        self.assertIn("macro_f1", res)
        self.assertEqual(res["model"], "TabPFNClassifier")

    def test_predict_level_1_reference(self):
        """In-distribution sample must yield normal prediction and Level 1 status."""
        data = CropInput(
            N=90.0,
            P=42.0,
            K=43.0,
            temperature=20.88,
            humidity=82.0,
            ph=6.5,
            rainfall=202.94,
        )
        res = main.predict(data)

        self.assertFalse(res["recommendation_withheld"])
        self.assertEqual(res["reliability_level"], "level_1_reference")
        self.assertNotEqual(res["predicted_crop"], "Recommendation Withheld")
        self.assertEqual(len(res["top_3"]), 3)
        self.assertEqual(res["top_3"][0]["crop"], res["predicted_crop"])
        self.assertEqual(res["input_validation"]["status"], "passed")
        self.assertEqual(res["input_validation"]["distribution_status"], "within_reference")

        # Verify all existing legacy response keys exist
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
            self.assertIn(key, res)

    def test_predict_level_2_unusual_extrapolation(self):
        """
        Input outside training range but within configurable guardrails must return
        prediction with warning, not withheld (safeguard #1).
        """
        # Rainfall 320 mm is outside observed max (298.56 mm) but plausible
        data = CropInput(
            N=90.0,
            P=42.0,
            K=43.0,
            temperature=20.88,
            humidity=82.0,
            ph=6.5,
            rainfall=320.0,
        )
        res = main.predict(data)

        self.assertFalse(res["recommendation_withheld"])
        self.assertEqual(res["reliability_level"], "level_2_unusual")
        self.assertEqual(len(res["top_3"]), 3)
        self.assertGreater(len(res["input_warnings"]), 0)
        self.assertTrue(
            any("rainfall" in w and "outside the observed" in w for w in res["input_warnings"])
        )

    def test_predict_level_3_severe_outlier_withheld(self):
        """
        Severely unfamiliar or unviable input (e.g. pH=13.0) must have recommendation withheld,
        empty top_3 list, and clear diagnostic reasons (safeguard #3).
        """
        data = CropInput(
            N=90.0,
            P=42.0,
            K=43.0,
            temperature=20.88,
            humidity=82.0,
            ph=13.0,  # Caustic, hostile to all crops
            rainfall=202.94,
        )
        res = main.predict(data)

        self.assertTrue(res["recommendation_withheld"])
        self.assertEqual(res["reliability_level"], "level_3_severe_or_invalid")
        self.assertEqual(res["predicted_crop"], "Recommendation Withheld")
        self.assertEqual(res["top_3"], [])
        self.assertTrue(res["input_validation"]["recommendation_withheld"])
        self.assertIn("Recommendation withheld", res["notice"])
        self.assertTrue(
            any("ph" in w for w in res["input_warnings"])
        )

    def test_explain_withheld_input_raises_http_400(self):
        """Calling /explain on a severely invalid/withheld input must raise HTTP 400."""
        data = CropInput(
            N=90.0,
            P=42.0,
            K=43.0,
            temperature=20.88,
            humidity=82.0,
            ph=13.0,
            rainfall=202.94,
        )
        with self.assertRaises(HTTPException) as ctx:
            main.explain(data)
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("recommendation is withheld", ctx.exception.detail)

    def test_historical_endpoints(self):
        """Verify historical endpoints return valid data structure."""
        ranking = main.historical_ranking(
            state="Andhra Pradesh",
            district="ANANTAPUR",
            season="Kharif",
            limit=5,
        )
        self.assertIn("crops", ranking)
        self.assertEqual(ranking["district"], "ANANTAPUR")

        trend = main.historical_trend(
            state="Andhra Pradesh",
            district="ANANTAPUR",
            crop="Groundnut",
            season="Kharif",
        )
        self.assertIn("trend", trend)
        self.assertEqual(trend["crop"], "Groundnut")


if __name__ == "__main__":
    unittest.main()
