
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler


FEATURES = [
    "N", "P", "K", "temperature",
    "humidity", "ph", "rainfall",
]

DEFAULT_PHYSICAL_LIMITS = {
    "N": (0.0, float("inf")),
    "P": (0.0, float("inf")),
    "K": (0.0, float("inf")),
    "temperature": (-273.15, 100.0),
    "humidity": (0.0, 100.0),
    "ph": (0.0, 14.0),
    "rainfall": (0.0, float("inf")),
}

DEFAULT_AGRONOMIC_GUARDRAILS = {
    "N": (0.0, 350.0),
    "P": (0.0, 250.0),
    "K": (0.0, 350.0),
    "temperature": (-10.0, 55.0),
    "humidity": (5.0, 100.0),
    "ph": (3.0, 10.5),
    "rainfall": (0.0, 1000.0),
}

DEFAULT_UNUSUAL_DISTANCE_THRESHOLD = 0.9158
DEFAULT_SEVERE_DISTANCE_THRESHOLD = 3.00


class CropInputValidator:

    def __init__(
        self,
        training_data: pd.DataFrame,
        physical_limits: Optional[Dict[str, tuple[float, float]]] = None,
        agronomic_guardrails: Optional[Dict[str, tuple[float, float]]] = None,
        unusual_distance_threshold: float = DEFAULT_UNUSUAL_DISTANCE_THRESHOLD,
        severe_distance_threshold: float = DEFAULT_SEVERE_DISTANCE_THRESHOLD,
    ):

        missing = set(FEATURES) - set(training_data.columns)

        if missing:
            raise ValueError(
                f"Dataset is missing required features: {sorted(missing)}"
            )

        values = training_data[FEATURES].apply(
            pd.to_numeric, errors="coerce"
        )

        if not np.isfinite(values.to_numpy()).all():
            raise ValueError(
                "Training features contain missing or non-finite values."
            )

        if len(values) < 6:
            raise ValueError(
                "At least 6 training records are required."
            )

        if (
            not np.isfinite(unusual_distance_threshold)
            or not np.isfinite(severe_distance_threshold)
            or unusual_distance_threshold <= 0
            or severe_distance_threshold <= unusual_distance_threshold
        ):
            raise ValueError("Invalid distance thresholds.")

        self.physical_limits = {
            **DEFAULT_PHYSICAL_LIMITS,
            **(physical_limits or {}),
        }

        self.agronomic_guardrails = {
            **DEFAULT_AGRONOMIC_GUARDRAILS,
            **(agronomic_guardrails or {}),
        }

        self.scaler = StandardScaler()
        scaled = self.scaler.fit_transform(values)

        self.ranges = {
            feature: {
                "min": float(values[feature].min()),
                "max": float(values[feature].max()),
            }
            for feature in FEATURES
        }

        self.neighbors_query = NearestNeighbors(n_neighbors=5)
        self.neighbors_query.fit(scaled)

        # sklearn excludes each training row itself when X is omitted.
        self.neighbors_train = NearestNeighbors(n_neighbors=5)
        self.neighbors_train.fit(scaled)

        training_distances, _ = self.neighbors_train.kneighbors()
        reference_scores = training_distances.mean(axis=1)

        self.training_distance_median = float(
            np.median(reference_scores)
        )
        self.training_distance_p95 = float(
            np.percentile(reference_scores, 95)
        )

        self.unusual_distance_threshold = float(
            unusual_distance_threshold
        )
        self.severe_distance_threshold = float(
            severe_distance_threshold
        )

        self.distance_threshold = self.unusual_distance_threshold

    def validate(self, input_values: Dict[str, Any]) -> Dict[str, Any]:

        if not isinstance(input_values, dict):
            raise ValueError("Input must be a dictionary.")

        warnings: List[str] = []
        violations: List[str] = []
        out_of_range_features: List[str] = []
        parsed_values = {}

        # 1. Validate required numeric inputs.
        for feature in FEATURES:

            if feature not in input_values:
                violations.append(
                    f"Missing required feature: '{feature}'."
                )
                continue

            raw_value = input_values[feature]

            try:
                value = float(raw_value)
            except (ValueError, TypeError):
                violations.append(
                    f"Feature '{feature}' has a non-numeric value."
                )
                continue

            if not np.isfinite(value):
                violations.append(
                    f"Feature '{feature}' must be a finite number."
                )
                continue

            parsed_values[feature] = value

        # Invalid inputs: withhold recommendation.
        if violations:
            return {
                "reliability_level": "level_3_severe_or_invalid",
                "status": "invalid",
                "range_status": "invalid",
                "distribution_status": "severely_unfamiliar",
                "recommendation_withheld": True,
                "nearest_neighbor_distance": None,
                "reference_distance_threshold": round(
                    self.unusual_distance_threshold, 6
                ),
                "severe_distance_threshold": round(
                    self.severe_distance_threshold, 6
                ),
                "warnings": violations,
                "violations": violations,
                "reasons": violations,
                "observed_ranges": self.ranges,
            }

        # 2. Physical limits and agronomic guardrails.
        for feature, value in parsed_values.items():

            low, high = self.physical_limits[feature]

            if not low <= value <= high:
                violations.append(
                    f"{feature}={value:g} violates physical limits "
                    f"({low:g} to {high:g})."
                )

            low, high = self.agronomic_guardrails[feature]

            if not low <= value <= high:
                violations.append(
                    f"{feature}={value:g} is outside agronomic "
                    f"guardrails ({low:g} to {high:g})."
                )

        # 3. Compare individual values with training ranges.
        for feature, value in parsed_values.items():

            limits = self.ranges[feature]

            if not limits["min"] <= value <= limits["max"]:
                out_of_range_features.append(feature)

                warnings.append(
                    f"{feature}={value:g} is outside the observed "
                    f"dataset range ({limits['min']:.3f} to "
                    f"{limits['max']:.3f})."
                )

        # 4. Evaluate multivariate familiarity.
        row = pd.DataFrame(
            [parsed_values],
            columns=FEATURES,
        )

        scaled_input = self.scaler.transform(row)

        distances, _ = self.neighbors_query.kneighbors(
            scaled_input
        )

        distance_score = float(distances[0].mean())

        is_severe_distance = (
            distance_score > self.severe_distance_threshold
        )
        is_unusual_distance = (
            distance_score > self.unusual_distance_threshold
        )

        if is_severe_distance:
            violations.append(
                f"The input combination is severely unfamiliar "
                f"(5-NN distance: {distance_score:.4f})."
            )

        elif is_unusual_distance:
            warnings.append(
                f"The input combination is unusual compared with "
                f"the reference dataset (5-NN distance: "
                f"{distance_score:.4f})."
            )

        # 5. Determine reliability level.
        if violations:

            reliability_level = "level_3_severe_or_invalid"
            recommendation_withheld = True

            range_status = (
                "invalid"
                if any(
                    "physical limits" in v or "guardrails" in v
                    for v in violations
                )
                else "warning"
            )

            distribution_status = (
                "severely_unfamiliar"
                if is_severe_distance
                else "within_reference"
            )

            all_messages = violations + warnings

        elif out_of_range_features or is_unusual_distance:

            reliability_level = "level_2_unusual"
            recommendation_withheld = False

            range_status = (
                "warning" if out_of_range_features else "passed"
            )

            distribution_status = (
                "unusual_combination"
                if is_unusual_distance
                else "within_reference"
            )

            all_messages = warnings

        else:

            reliability_level = "level_1_reference"
            recommendation_withheld = False
            range_status = "passed"
            distribution_status = "within_reference"
            all_messages = []

        return {
            "reliability_level": reliability_level,
            "status": range_status,
            "range_status": range_status,
            "distribution_status": distribution_status,
            "recommendation_withheld": recommendation_withheld,
            "nearest_neighbor_distance": round(distance_score, 6),
            "reference_distance_threshold": round(
                self.unusual_distance_threshold, 6
            ),
            "severe_distance_threshold": round(
                self.severe_distance_threshold, 6
            ),
            "warnings": all_messages,
            "violations": violations,
            "reasons": violations if violations else warnings,
            "observed_ranges": self.ranges,
        }
