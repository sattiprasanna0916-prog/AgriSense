
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
)

from tabpfn import TabPFNClassifier


# =====================================================
# PATHS AND CONFIGURATION
# =====================================================

BASE_DIR = Path(__file__).resolve().parent

DATA_PATH = (
    BASE_DIR
    / "data"
    / "raw"
    / "Crop_recommendation.csv"
)

ARTIFACT_DIR = BASE_DIR / "artifacts"
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_PATH = ARTIFACT_DIR / "tabpfn_cv_metrics.json"

FEATURES = [
    "N",
    "P",
    "K",
    "temperature",
    "humidity",
    "ph",
    "rainfall",
]

RANDOM_STATE = 42
N_SPLITS = 5


# =====================================================
# MAIN FUNCTION
# =====================================================

def main():

    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Dataset not found: {DATA_PATH}"
        )

    print("Loading dataset...")

    df = pd.read_csv(DATA_PATH)

    required_columns = FEATURES + ["label"]

    missing_columns = (
        set(required_columns) - set(df.columns)
    )

    if missing_columns:
        raise ValueError(
            f"Missing columns: {sorted(missing_columns)}"
        )

    if df.empty:
        raise ValueError("Dataset is empty.")

    if df[required_columns].isnull().any().any():
        raise ValueError(
            "Dataset contains missing values."
        )

    X = df[FEATURES].apply(
        pd.to_numeric,
        errors="raise",
    )

    y = df["label"].astype(str)

    if not np.isfinite(X.to_numpy(dtype=float)).all():
        raise ValueError(
            "Dataset contains non-finite feature values."
        )

    print(f"Total records: {len(df)}")
    print(f"Training features: {len(FEATURES)}")
    print(f"Crop classes: {y.nunique()}")

    # =================================================
    # STRATIFIED CROSS-VALIDATION
    # =================================================

    cv = StratifiedKFold(
        n_splits=N_SPLITS,
        shuffle=True,
        random_state=RANDOM_STATE,
    )

    fold_results = []

    for fold, (train_idx, test_idx) in enumerate(
        cv.split(X, y),
        start=1,
    ):

        X_train = X.iloc[train_idx]
        X_test = X.iloc[test_idx]

        y_train = y.iloc[train_idx]
        y_test = y.iloc[test_idx]

        print(
            f"\nFold {fold}/{N_SPLITS}: "
            "training TabPFN..."
        )

        model = TabPFNClassifier(device="auto")

        # ---------------------------------------------
        # TRAINING
        # ---------------------------------------------

        start = time.perf_counter()

        model.fit(X_train, y_train)

        training_seconds = (
            time.perf_counter() - start
        )

        # ---------------------------------------------
        # PREDICTION
        # ---------------------------------------------

        start = time.perf_counter()

        predictions = model.predict(X_test)

        inference_seconds = (
            time.perf_counter() - start
        )

        # ---------------------------------------------
        # EVALUATION
        # ---------------------------------------------

        result = {
            "fold": fold,

            "accuracy": float(
                accuracy_score(y_test, predictions)
            ),

            "macro_precision": float(
                precision_score(
                    y_test,
                    predictions,
                    average="macro",
                    zero_division=0,
                )
            ),

            "macro_recall": float(
                recall_score(
                    y_test,
                    predictions,
                    average="macro",
                    zero_division=0,
                )
            ),

            "macro_f1": float(
                f1_score(
                    y_test,
                    predictions,
                    average="macro",
                    zero_division=0,
                )
            ),

            "training_seconds": round(
                training_seconds,
                2,
            ),

            "inference_seconds": round(
                inference_seconds,
                2,
            ),
        }

        fold_results.append(result)

        print(
            f"Accuracy: {result['accuracy']:.4f} | "
            f"Macro F1: {result['macro_f1']:.4f} | "
            f"Inference: {inference_seconds:.2f}s"
        )

    # =================================================
    # SUMMARY
    # =================================================

    metric_names = [
        "accuracy",
        "macro_precision",
        "macro_recall",
        "macro_f1",
    ]

    summary = {
        "model": "TabPFNClassifier",
        "dataset": DATA_PATH.name,
        "evaluation_method": "StratifiedKFold",
        "folds": N_SPLITS,
        "random_state": RANDOM_STATE,
        "total_records": int(len(df)),
        "number_of_classes": int(y.nunique()),
        "fold_results": fold_results,
        "summary": {},
    }

    for metric in metric_names:

        values = [
            item[metric]
            for item in fold_results
        ]

        summary["summary"][metric] = {
            "mean": float(np.mean(values)),
            "std": float(np.std(values, ddof=1)),
        }

        print(
            f"\n{metric}: "
            f"mean={summary['summary'][metric]['mean']:.4f}, "
            f"std={summary['summary'][metric]['std']:.4f}"
        )

    # =================================================
    # SAVE RESULTS
    # =================================================

    with OUTPUT_PATH.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            summary,
            file,
            indent=2,
        )

    print(f"\nSaved results to: {OUTPUT_PATH}")

    print("\nTabPFN cross-validation completed.")


if __name__ == "__main__":
    main()
