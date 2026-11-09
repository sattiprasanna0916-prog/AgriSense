
"""
derive_validation_thresholds.py
--------------------------------

Derives agricultural input familiarity thresholds using
leakage-controlled 5-fold cross-validation on the training
partition of Crop_recommendation.csv.

The held-out test partition is used only for independent
evaluation of the selected thresholds.

Threshold policy:
- Unusual threshold: empirically derived from OOF training distances.
- Severe threshold: manually configured policy threshold (3.00).
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd

from sklearn.model_selection import (
    StratifiedKFold,
    train_test_split,
)
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler


# =========================================================
# 1. CONFIGURATION
# =========================================================

BASE_DIR = Path(__file__).resolve().parent

DATA_PATH = (
    BASE_DIR
    / "data"
    / "raw"
    / "Crop_recommendation.csv"
)

OUTPUT_PATH = (
    BASE_DIR
    / "artifacts"
    / "reliability_thresholds.json"
)

FEATURES = [
    "N",
    "P",
    "K",
    "temperature",
    "humidity",
    "ph",
    "rainfall",
]

TARGET = "label"

RANDOM_STATE = 42
TEST_SIZE = 0.20
CV_FOLDS = 5
K_NEIGHBORS = 5

# Manually configured policy threshold.
# This is NOT derived from the held-out test set.
SEVERE_THRESHOLD = 3.00


# =========================================================
# 2. DATASET VALIDATION
# =========================================================

def load_dataset():

    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Dataset not found: {DATA_PATH}"
        )

    df = pd.read_csv(DATA_PATH)

    required_columns = FEATURES + [TARGET]

    missing_columns = [
        col for col in required_columns
        if col not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {missing_columns}"
        )

    X = df[FEATURES].apply(
        pd.to_numeric,
        errors="coerce"
    )

    y = df[TARGET]

    if X.isna().any().any():
        raise ValueError(
            "Dataset contains missing or non-numeric feature values."
        )

    if not np.isfinite(
        X.to_numpy(dtype=float)
    ).all():
        raise ValueError(
            "Dataset contains infinite feature values."
        )

    if y.isna().any():
        raise ValueError(
            "Dataset contains missing crop labels."
        )

    y = y.astype(str)

    class_counts = y.value_counts()

    if class_counts.min() < CV_FOLDS:
        raise ValueError(
            f"Each crop class needs at least {CV_FOLDS} records "
            "for stratified cross-validation."
        )

    return X, y


# =========================================================
# 3. NEAREST-NEIGHBOR DISTANCE CALCULATION
# =========================================================

def calculate_mean_neighbor_distances(
    reference_data,
    query_data,
    k_neighbors,
):

    if len(reference_data) < k_neighbors:
        raise ValueError(
            "Reference dataset contains fewer records "
            "than the requested number of neighbors."
        )

    neighbors = NearestNeighbors(
        n_neighbors=k_neighbors
    )

    neighbors.fit(reference_data)

    distances, _ = neighbors.kneighbors(query_data)

    return distances.mean(axis=1)


# =========================================================
# 4. THRESHOLD DERIVATION
# =========================================================

def derive_thresholds():

    X, y = load_dataset()

    # -----------------------------------------------------
    # Reproduce the training split from train_model.py
    # -----------------------------------------------------

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
        stratify=y,
    )

    print("\n========== DATASET INFORMATION ==========")

    print("Dataset:", DATA_PATH.name)
    print("Total dataset records:", len(X))
    print("Training split records:", len(X_train))
    print("Held-out test records:", len(X_test))
    print("Crop classes:", y.nunique())
    print("Features:", FEATURES)

    # -----------------------------------------------------
    # 5-fold cross-validation on training partition only
    # -----------------------------------------------------

    print("\n========== CROSS-VALIDATION ==========")

    skf = StratifiedKFold(
        n_splits=CV_FOLDS,
        shuffle=True,
        random_state=RANDOM_STATE,
    )

    oof_distances = []

    for fold, (train_idx, val_idx) in enumerate(
        skf.split(X_train, y_train),
        start=1,
    ):

        fold_train = X_train.iloc[train_idx]
        fold_val = X_train.iloc[val_idx]

        # Fit scaler exclusively on fold training data.
        scaler = StandardScaler()

        scaled_train = scaler.fit_transform(
            fold_train
        )

        scaled_val = scaler.transform(
            fold_val
        )

        # Calculate distance to five nearest training samples.
        fold_distances = calculate_mean_neighbor_distances(
            reference_data=scaled_train,
            query_data=scaled_val,
            k_neighbors=K_NEIGHBORS,
        )

        oof_distances.extend(
            fold_distances.tolist()
        )

        print(
            f"Fold {fold}: "
            f"training={len(train_idx)}, "
            f"validation={len(val_idx)}, "
            f"samples={len(fold_distances)}"
        )

    oof_distances = np.asarray(
        oof_distances,
        dtype=float,
    )

    if len(oof_distances) != len(X_train):
        raise RuntimeError(
            "Out-of-fold distance count does not match "
            "the training partition size."
        )

    # -----------------------------------------------------
    # Calculate OOF training percentiles
    # -----------------------------------------------------

    percentiles = {
        "p50": float(np.percentile(oof_distances, 50.0)),
        "p75": float(np.percentile(oof_distances, 75.0)),
        "p90": float(np.percentile(oof_distances, 90.0)),
        "p95": float(np.percentile(oof_distances, 95.0)),
        "p97_5": float(np.percentile(oof_distances, 97.5)),
        "p99": float(np.percentile(oof_distances, 99.0)),
        "p99_5": float(np.percentile(oof_distances, 99.5)),
        "p99_8": float(np.percentile(oof_distances, 99.8)),
        "max": float(np.max(oof_distances)),
    }

    q25 = float(
        np.percentile(oof_distances, 25.0)
    )

    q75 = percentiles["p75"]

    iqr = q75 - q25

    # -----------------------------------------------------
    # Derive unusual threshold from OOF training data
    # -----------------------------------------------------

    threshold_unusual = round(
        percentiles["p95"],
        4,
    )

    # -----------------------------------------------------
    # Severe threshold is a manual policy setting
    # -----------------------------------------------------

    threshold_severe = SEVERE_THRESHOLD

    if threshold_severe <= threshold_unusual:
        raise ValueError(
            "Severe threshold must be greater than "
            "the unusual threshold."
        )

    # -----------------------------------------------------
    # Independent held-out test evaluation
    # -----------------------------------------------------

    print("\n========== HELD-OUT TEST EVALUATION ==========")

    scaler_full_train = StandardScaler()

    scaled_full_train = scaler_full_train.fit_transform(
        X_train
    )

    scaled_test = scaler_full_train.transform(
        X_test
    )

    test_scores = calculate_mean_neighbor_distances(
        reference_data=scaled_full_train,
        query_data=scaled_test,
        k_neighbors=K_NEIGHBORS,
    )

    false_warning_rate = float(
        (test_scores > threshold_unusual).mean() * 100
    )

    false_rejection_rate = float(
        (test_scores > threshold_severe).mean() * 100
    )

    # -----------------------------------------------------
    # Construct output documentation
    # -----------------------------------------------------

    results = {

        "dataset": DATA_PATH.name,

        "k_neighbors": K_NEIGHBORS,

        "cv_folds": CV_FOLDS,

        "random_state": RANDOM_STATE,

        "training_records": len(X_train),

        "test_records": len(X_test),

        "out_of_fold_distance_percentiles": percentiles,

        "iqr": round(iqr, 4),

        "tukey_mild_fence_q75_plus_1_5_iqr": round(
            q75 + 1.5 * iqr,
            4,
        ),

        "tukey_extreme_fence_q75_plus_3_0_iqr": round(
            q75 + 3.0 * iqr,
            4,
        ),

        "selected_thresholds": {

            "threshold_unusual": threshold_unusual,

            "threshold_severe": threshold_severe,
        },

        "empirical_test_set_evaluation": {

            "test_sample_count": len(X_test),

            "test_max_distance": round(
                float(np.max(test_scores)),
                4,
            ),

            "test_mean_distance": round(
                float(np.mean(test_scores)),
                4,
            ),

            "false_warning_rate_at_unusual_threshold_pct": round(
                false_warning_rate,
                2,
            ),

            "false_rejection_rate_at_severe_threshold_pct": round(
                false_rejection_rate,
                2,
            ),
        },

        "notes": (
            "The unusual threshold was derived from the "
            "95th percentile of out-of-fold training distances. "
            "The severe threshold of 3.00 is a manually selected "
            "policy threshold, not an empirically derived percentile. "
            "The held-out test partition was used only to evaluate "
            "the selected thresholds."
        ),
    }

    # -----------------------------------------------------
    # Save threshold documentation
    # -----------------------------------------------------

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with OUTPUT_PATH.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            results,
            file,
            indent=2,
        )

    # -----------------------------------------------------
    # Final report
    # -----------------------------------------------------

    print("\n========== RELIABILITY THRESHOLD DERIVATION COMPLETE ==========")

    print(
        "Unusual Distance Threshold:",
        threshold_unusual,
    )

    print(
        "Severe Distance Threshold:",
        threshold_severe,
    )

    print(
        "Held-out test false warning rate:",
        f"{false_warning_rate:.2f}%",
    )

    print(
        "Held-out test false rejection rate:",
        f"{false_rejection_rate:.2f}%",
    )

    print(
        "Held-out test maximum distance:",
        round(float(np.max(test_scores)), 4),
    )

    print(
        "Saved threshold documentation to:",
        OUTPUT_PATH,
    )

    print(
        "\nNote: The severe threshold is a policy choice. "
        "Its test-set rejection rate is an observed evaluation "
        "result, not a guarantee of detecting all invalid inputs."
    )

    return results


# =========================================================
# 5. EXECUTION
# =========================================================

if __name__ == "__main__":
    derive_thresholds()
