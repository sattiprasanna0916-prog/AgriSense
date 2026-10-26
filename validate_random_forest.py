
import json
from pathlib import Path

import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedKFold, cross_validate
from sklearn.metrics import make_scorer, precision_score, recall_score, f1_score

BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data" / "raw" / "Crop_recommendation.csv"
ARTIFACT_DIR = BASE_DIR / "artifacts"
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

FEATURES = [
    "N", "P", "K", "temperature",
    "humidity", "ph", "rainfall",
]


def main():
    df = pd.read_csv(DATA_PATH)

    X = df[FEATURES].apply(pd.to_numeric, errors="raise")
    y = df["label"].astype(str)

    cv = StratifiedKFold(
        n_splits=5,
        shuffle=True,
        random_state=42,
    )

    model = RandomForestClassifier(
        n_estimators=300,
        random_state=42,
        n_jobs=-1,
    )

    scoring = {
        "accuracy": "accuracy",
        "macro_precision": make_scorer(
            precision_score, average="macro", zero_division=0
        ),
        "macro_recall": make_scorer(
            recall_score, average="macro", zero_division=0
        ),
        "macro_f1": make_scorer(
            f1_score, average="macro", zero_division=0
        ),
    }

    print("Running 5-fold stratified cross-validation...")
    results = cross_validate(
        model,
        X,
        y,
        cv=cv,
        scoring=scoring,
        n_jobs=1,
        return_train_score=False,
    )

    summary = {}

    for metric in scoring:
        values = results[f"test_{metric}"]
        summary[metric] = {
            "fold_scores": [round(float(v), 6) for v in values],
            "mean": float(values.mean()),
            "std": float(values.std(ddof=1)),
        }

        print(f"\n{metric}:")
        print("  Fold scores:", summary[metric]["fold_scores"])
        print(f"  Mean: {values.mean():.4f}")
        print(f"  Standard deviation: {values.std(ddof=1):.4f}")

    output_path = ARTIFACT_DIR / "random_forest_cv_metrics.json"

    with output_path.open("w", encoding="utf-8") as file:
        json.dump(summary, file, indent=2)

    print(f"\nSaved cross-validation results to: {output_path}")


if __name__ == "__main__":
    main()
