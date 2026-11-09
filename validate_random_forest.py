
import json
from pathlib import Path

import pandas as pd

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedKFold, cross_validate
from sklearn.metrics import (
    make_scorer,
    precision_score,
    recall_score,
    f1_score,
)


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

OUTPUT_PATH = (
    ARTIFACT_DIR / "random_forest_cv_metrics.json"
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

    print(f"Total records: {len(df)}")
    print(f"Crop classes: {y.nunique()}")

    # =================================================
    # CROSS-VALIDATION
    # =================================================

    cv = StratifiedKFold(
        n_splits=N_SPLITS,
        shuffle=True,
        random_state=RANDOM_STATE,
    )

    model = RandomForestClassifier(
        n_estimators=300,
        random_state=RANDOM_STATE,
        n_jobs=-1,
    )

    scoring = {
        "accuracy": "accuracy",

        "macro_precision": make_scorer(
            precision_score,
            average="macro",
            zero_division=0,
        ),

        "macro_recall": make_scorer(
            recall_score,
            average="macro",
            zero_division=0,
        ),

        "macro_f1": make_scorer(
            f1_score,
            average="macro",
            zero_division=0,
        ),
    }

    print(
        f"\nRunning {N_SPLITS}-fold stratified "
        "cross-validation..."
    )

    results = cross_validate(
        model,
        X,
        y,
        cv=cv,
        scoring=scoring,
        n_jobs=1,
        return_train_score=False,
        error_score="raise",
    )

    # =================================================
    # SUMMARIZE RESULTS
    # =================================================

    summary = {
        "model": "RandomForestClassifier",
        "dataset": DATA_PATH.name,
        "evaluation_method": "StratifiedKFold",
        "number_of_folds": N_SPLITS,
        "random_state": RANDOM_STATE,
        "total_records": int(len(df)),
        "number_of_classes": int(y.nunique()),
        "metrics": {},
    }

    for metric in scoring:

        values = results[f"test_{metric}"]

        summary["metrics"][metric] = {
            "fold_scores": [
                round(float(value), 6)
                for value in values
            ],
            "mean": float(values.mean()),
            "std": float(values.std(ddof=1)),
        }

        print(f"\n{metric}:")
        print(
            "  Fold scores:",
            summary["metrics"][metric]["fold_scores"],
        )
        print(f"  Mean: {values.mean():.4f}")
        print(
            f"  Standard deviation: "
            f"{values.std(ddof=1):.4f}"
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

    print(
        f"\nSaved cross-validation results to: "
        f"{OUTPUT_PATH}"
    )

    print("\nRandom Forest validation completed.")


if __name__ == "__main__":
    main()
