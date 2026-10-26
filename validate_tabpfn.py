
import json
import time
from pathlib import Path

import pandas as pd
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
)
from tabpfn import TabPFNClassifier

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

    fold_results = []

    for fold, (train_idx, test_idx) in enumerate(
        cv.split(X, y), start=1
    ):
        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]

        print(f"\nFold {fold}/5: training TabPFN...")
        model = TabPFNClassifier(device="auto")

        start = time.perf_counter()
        model.fit(X_train, y_train)
        training_seconds = time.perf_counter() - start

        start = time.perf_counter()
        predictions = model.predict(X_test)
        inference_seconds = time.perf_counter() - start

        result = {
            "fold": fold,
            "accuracy": float(accuracy_score(y_test, predictions)),
            "macro_precision": float(
                precision_score(
                    y_test, predictions,
                    average="macro", zero_division=0
                )
            ),
            "macro_recall": float(
                recall_score(
                    y_test, predictions,
                    average="macro", zero_division=0
                )
            ),
            "macro_f1": float(
                f1_score(
                    y_test, predictions,
                    average="macro", zero_division=0
                )
            ),
            "training_seconds": round(training_seconds, 2),
            "inference_seconds": round(inference_seconds, 2),
        }

        fold_results.append(result)

        print(
            f"Accuracy: {result['accuracy']:.4f} | "
            f"Macro F1: {result['macro_f1']:.4f} | "
            f"Inference: {inference_seconds:.2f}s"
        )

    metric_names = [
        "accuracy",
        "macro_precision",
        "macro_recall",
        "macro_f1",
    ]

    summary = {
        "model": "TabPFNClassifier",
        "dataset": DATA_PATH.name,
        "folds": 5,
        "random_state": 42,
        "fold_results": fold_results,
        "summary": {},
    }

    for metric in metric_names:
        values = [item[metric] for item in fold_results]
        summary["summary"][metric] = {
            "mean": float(pd.Series(values).mean()),
            "std": float(pd.Series(values).std(ddof=1)),
        }

        print(
            f"{metric}: mean={summary['summary'][metric]['mean']:.4f}, "
            f"std={summary['summary'][metric]['std']:.4f}"
        )

    output_path = ARTIFACT_DIR / "tabpfn_cv_metrics.json"
    with output_path.open("w", encoding="utf-8") as file:
        json.dump(summary, file, indent=2)

    print(f"\nSaved results to: {output_path}")


if __name__ == "__main__":
    main()
