"""
input_validation.py
-------------------
Multi-level input validation and reliability assessment for crop recommendation.

Distinguishes:
1. Physically invalid or non-finite inputs.
2. Extreme configurable agronomic guardrails (data-entry errors / unviable conditions).
3. Values outside the observed dataset training ranges (univariate extrapolation).
4. Inside-range unusual multivariate combinations.
5. In-distribution reference inputs.

Three-level reliability policy:
- Level 1 (Within reference distribution): Display recommendation normally.
- Level 2 (Unusual input combination): Display recommendation with clear warning.
- Level 3 (Severely unfamiliar or invalid input): Withhold recommendation and guide verification.
"""

from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler

FEATURES = [
    "N",
    "P",
    "K",
    "temperature",
    "humidity",
    "ph",
    "rainfall",
]

# Physical hard limits: values outside these bounds are scientifically impossible.
DEFAULT_PHYSICAL_LIMITS: Dict[str, tuple[float, float]] = {
    "N": (0.0, float("inf")),
    "P": (0.0, float("inf")),
    "K": (0.0, float("inf")),
    "temperature": (-273.15, 100.0),
    "humidity": (0.0, 100.0),
    "ph": (0.0, 14.0),
    "rainfall": (0.0, float("inf")),
}

# Configurable agronomic guardrails: values outside these represent likely
# data-entry errors or extreme conditions where agricultural production is not viable.
# These are heuristic decision-support guardrails, not universal scientific laws.
DEFAULT_AGRONOMIC_GUARDRAILS: Dict[str, tuple[float, float]] = {
    "N": (0.0, 350.0),           # kg/ha
    "P": (0.0, 250.0),           # kg/ha
    "K": (0.0, 350.0),           # kg/ha
    "temperature": (-10.0, 55.0), # °C
    "humidity": (5.0, 100.0),    # %
    "ph": (3.0, 10.5),           # soil pH
    "rainfall": (0.0, 1000.0),   # mm per growing cycle
}

# Leakage-free cross-validation derived default distance thresholds
DEFAULT_UNUSUAL_DISTANCE_THRESHOLD = 0.9158
DEFAULT_SEVERE_DISTANCE_THRESHOLD = 3.00


class CropInputValidator:
    """
    Validates agricultural inputs across physical feasibility, dataset coverage,
    and multivariate density familiarity.
    """

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

        values = training_data[FEATURES].astype(float)

        if not np.isfinite(values.to_numpy()).all():
            raise ValueError("Training features contain non-finite values.")

        if len(values) < 6:
            raise ValueError(
                "At least 6 complete records are required for validation."
            )

        self.physical_limits = physical_limits or DEFAULT_PHYSICAL_LIMITS
        self.agronomic_guardrails = (
            agronomic_guardrails or DEFAULT_AGRONOMIC_GUARDRAILS
        )

        self.scaler = StandardScaler()
        scaled = self.scaler.fit_transform(values)

        # Observed empirical ranges in reference dataset
        self.ranges = {
            feature: {
                "min": float(training_data[feature].min()),
                "max": float(training_data[feature].max()),
            }
            for feature in FEATURES
        }

        # Fit NearestNeighbors for query evaluation (k=5 neighbors)
        self.neighbors_query = NearestNeighbors(n_neighbors=5)
        self.neighbors_query.fit(scaled)

        # Self-exclusion reference scores for training instances
        self.neighbors_train = NearestNeighbors(n_neighbors=6)
        self.neighbors_train.fit(scaled)
        training_distances, _ = self.neighbors_train.kneighbors(scaled)
        # Average distance to 5 nearest distinct neighbors (excluding self at index 0)
        reference_scores = training_distances[:, 1:6].mean(axis=1)

        self.training_distance_median = float(np.median(reference_scores))
        self.training_distance_p95 = float(np.percentile(reference_scores, 95.0))

        self.unusual_distance_threshold = float(unusual_distance_threshold)
        self.severe_distance_threshold = float(severe_distance_threshold)

        # Retain backwards-compatible property
        self.distance_threshold = self.unusual_distance_threshold

    def validate(self, input_values: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validates input dictionary and returns a three-level reliability evaluation.
        """
        warnings: List[str] = []
        violations: List[str] = []
        out_of_range_features: List[str] = []

        # 1. Non-finite / Type Feasibility Check
        parsed_values: Dict[str, float] = {}
        for feature in FEATURES:
            if feature not in input_values:
                violations.append(f"Missing required feature: '{feature}'.")
                continue

            raw_val = input_values[feature]
            try:
                num_val = float(raw_val)
            except (ValueError, TypeError):
                violations.append(
                    f"Feature '{feature}' has non-numeric value: {raw_val!r}."
                )
                continue

            if not np.isfinite(num_val):
                violations.append(
                    f"Feature '{feature}' must be a finite number; got {num_val}."
                )
                continue

            parsed_values[feature] = num_val

        # Immediate Level 3 return if non-finite or missing
        if violations or len(parsed_values) != len(FEATURES):
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

        # 2. Physical Limits Check (Impossible values)
        for feature, val in parsed_values.items():
            low, high = self.physical_limits.get(feature, (-float("inf"), float("inf")))
            if not (low <= val <= high):
                violations.append(
                    f"{feature}={val:g} violates physical feasibility bounds "
                    f"({low:g} to {high:g})."
                )

        # 3. Agronomic Guardrails Check (Severe outliers / entry errors)
        for feature, val in parsed_values.items():
            low, high = self.agronomic_guardrails.get(
                feature, (-float("inf"), float("inf"))
            )
            if not (low <= val <= high):
                violations.append(
                    f"{feature}={val:g} is outside viable agricultural guardrails "
                    f"({low:g} to {high:g})."
                )

        # 4. Observed Training Range Check (Univariate coverage)
        for feature, val in parsed_values.items():
            limits = self.ranges[feature]
            if not (limits["min"] <= val <= limits["max"]):
                out_of_range_features.append(feature)
                warnings.append(
                    f"{feature}={val:g} is outside the observed dataset range "
                    f"({limits['min']:.3f} to {limits['max']:.3f})."
                )

        # 5. Multivariate Distance Familiarity Check
        row = pd.DataFrame(
            [{feature: parsed_values[feature] for feature in FEATURES}],
            columns=FEATURES,
        )
        scaled_input = self.scaler.transform(row)
        distances, _ = self.neighbors_query.kneighbors(scaled_input)
        distance_score = float(distances[0].mean())

        is_severe_distance = distance_score > self.severe_distance_threshold
        is_unusual_distance = distance_score > self.unusual_distance_threshold

        if is_severe_distance:
            violations.append(
                f"The combination of inputs is severely unfamiliar "
                f"(standardized 5-NN distance: {distance_score:.4f}, exceeding "
                f"severe threshold {self.severe_distance_threshold:.4f})."
            )
        elif is_unusual_distance:
            warnings.append(
                f"The combination of inputs is unusual compared with the reference "
                f"dataset (5-NN distance: {distance_score:.4f} > {self.unusual_distance_threshold:.4f}). "
                "The model is extrapolating beyond familiar clusters."
            )

        # 6. Synthesize Three-Level Policy Decision
        if violations:
            # Level 3: Severely unfamiliar or invalid input
            reliability_level = "level_3_severe_or_invalid"
            recommendation_withheld = True
            range_status = "invalid" if any("physical" in v or "guardrails" in v for v in violations) else "warning"
            distribution_status = "severely_unfamiliar"
            all_messages = violations + warnings
        elif out_of_range_features or is_unusual_distance:
            # Level 2: Unusual input combination
            reliability_level = "level_2_unusual"
            recommendation_withheld = False
            range_status = "warning" if out_of_range_features else "passed"
            distribution_status = (
                "unusual_combination" if is_unusual_distance else "within_reference"
            )
            all_messages = warnings
        else:
            # Level 1: Within reference distribution
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
