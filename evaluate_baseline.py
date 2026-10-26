
import json
import time
from pathlib import Path

import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    classification_report,
    confusion_matrix,
)
from sklearn.model_selection import train_test_split


BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data" / "raw" / "Crop_recommendation.csv"
ARTIFACT_DIR = BASE_DIR / "artifacts"
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

RANDOM_STATE = 42
TEST_SIZE = 0.20

FEATURES = [
    "N",
    "P",
    "K",
    "temperature",
    "humidity",
    "ph",
    "rainfall",
]


def main():
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Dataset not found: {DATA_PATH}")

    df = pd.read_csv(DATA_PATH)

    expected_columns = FEATURES + ["label"]
    if list(df.columns) != expected_columns:
        raise ValueError(f"Unexpected dataset columns: {list(df.columns)}")

    if df.isnull().any().any():
        raise ValueError("Dataset contains missing values.")

    X = df[FEATURES].apply(pd.to_numeric, errors="raise")
    y = df["label"].astype(str)

    # Use exactly the same split settings as train_model.py.
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
        stratify=y,
    )

    model = RandomForestClassifier(
        n_estimators=300,
        random_state=RANDOM_STATE,
        class_weight=None,
        n_jobs=-1,
    )

    print("Training Random Forest baseline...")
    start = time.perf_counter()
    model.fit(X_train, y_train)
    training_seconds = time.perf_counter() - start

    start = time.perf_counter()
    predictions = model.predict(X_test)
    inference_seconds = time.perf_counter() - start

    metrics = {
        "model": "RandomForestClassifier",
        "dataset": DATA_PATH.name,
        "random_state": RANDOM_STATE,
        "test_size": TEST_SIZE,
        "total_records": int(len(df)),
        "training_records": int(len(X_train)),
        "test_records": int(len(X_test)),
        "number_of_classes": int(y.nunique()),
        "accuracy": float(accuracy_score(y_test, predictions)),
        "macro_precision": float(
            precision_score(y_test, predictions, average="macro", zero_division=0)
        ),
        "macro_recall": float(
            recall_score(y_test, predictions, average="macro", zero_division=0)
        ),
        "macro_f1": float(
            f1_score(y_test, predictions, average="macro", zero_division=0)
        ),
        "weighted_f1": float(
            f1_score(y_test, predictions, average="weighted", zero_division=0)
        ),
        "training_seconds": round(training_seconds, 2),
        "inference_seconds_for_test_set": round(inference_seconds, 2),
        "classification_report": classification_report(
            y_test,
            predictions,
            labels=sorted(y.unique()),
            output_dict=True,
            zero_division=0,
        ),
        "confusion_matrix": confusion_matrix(
            y_test, predictions, labels=sorted(y.unique())
        ).tolist(),
        "class_names": sorted(y.unique()),
    }

    output_path = ARTIFACT_DIR / "random_forest_metrics.json"
    with output_path.open("w", encoding="utf-8") as file:
        json.dump(metrics, file, indent=2)

    print("\n=== RANDOM FOREST TEST RESULTS ===")
    print(f"Accuracy:        {metrics['accuracy']:.4f}")
    print(f"Macro precision: {metrics['macro_precision']:.4f}")
    print(f"Macro recall:    {metrics['macro_recall']:.4f}")
    print(f"Macro F1:        {metrics['macro_f1']:.4f}")
    print(f"Weighted F1:     {metrics['weighted_f1']:.4f}")
    print(f"Training time:   {training_seconds:.2f} seconds")
    print(f"Test inference:  {inference_seconds:.2f} seconds")
    print("\nPer-class report:")
    print(classification_report(y_test, predictions, zero_division=0))
    print(f"\nMetrics saved to: {output_path}")


if __name__ == "__main__":
    main()
