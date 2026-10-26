
import json
import time
from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import pandas as pd

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    classification_report,
    confusion_matrix,
    ConfusionMatrixDisplay,
)
from sklearn.model_selection import train_test_split
from tabpfn import TabPFNClassifier


# Project paths
BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data" / "raw" / "Crop_recommendation.csv"
MODEL_DIR = BASE_DIR / "models"
ARTIFACT_DIR = BASE_DIR / "artifacts"

MODEL_DIR.mkdir(parents=True, exist_ok=True)
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
        raise FileNotFoundError(
            f"Dataset not found: {DATA_PATH}"
        )

    print("Loading dataset...")
    df = pd.read_csv(DATA_PATH)

    expected_columns = FEATURES + ["label"]
    if list(df.columns) != expected_columns:
        raise ValueError(
            f"Unexpected dataset columns: {list(df.columns)}"
        )

    if df.isnull().any().any():
        raise ValueError(
            "Dataset contains missing values."
        )

    X = df[FEATURES].apply(pd.to_numeric, errors="raise")
    y = df["label"].astype(str)

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
        stratify=y,
    )

    print(f"Total records: {len(df)}")
    print(f"Training records: {len(X_train)}")
    print(f"Test records: {len(X_test)}")
    print(f"Crop classes: {y.nunique()}")

    print("\nInitializing TabPFN...")
    model = TabPFNClassifier(device="auto")

    print("Training model. This may take some time...")
    start = time.perf_counter()
    model.fit(X_train, y_train)
    training_seconds = time.perf_counter() - start

    print("Generating test predictions...")
    inference_start = time.perf_counter()
    y_pred = model.predict(X_test)
    inference_seconds = time.perf_counter() - inference_start

    metrics = {
        "model": "TabPFNClassifier",
        "dataset": DATA_PATH.name,
        "random_state": RANDOM_STATE,
        "test_size": TEST_SIZE,
        "total_records": int(len(df)),
        "training_records": int(len(X_train)),
        "test_records": int(len(X_test)),
        "number_of_classes": int(y.nunique()),
        "accuracy": float(accuracy_score(y_test, y_pred)),
        "macro_precision": float(
            precision_score(
                y_test, y_pred, average="macro", zero_division=0
            )
        ),
        "macro_recall": float(
            recall_score(
                y_test, y_pred, average="macro", zero_division=0
            )
        ),
        "macro_f1": float(
            f1_score(
                y_test, y_pred, average="macro", zero_division=0
            )
        ),
        "weighted_f1": float(
            f1_score(
                y_test, y_pred, average="weighted", zero_division=0
            )
        ),
        "training_seconds": round(training_seconds, 2),
        "inference_seconds_for_test_set": round(
            inference_seconds, 2
        ),
    }

    report = classification_report(
        y_test,
        y_pred,
        labels=sorted(y.unique()),
        output_dict=True,
        zero_division=0,
    )

    metrics["classification_report"] = report

    # Save model and evaluation results
    joblib.dump(model, MODEL_DIR / "tabpfn_crop_model.joblib")

    with (ARTIFACT_DIR / "evaluation_metrics.json").open(
        "w", encoding="utf-8"
    ) as file:
        json.dump(metrics, file, indent=2)

    # Save the exact test split and predictions for reproducibility
    test_results = X_test.copy()
    test_results["actual_crop"] = y_test
    test_results["predicted_crop"] = y_pred
    test_results.to_csv(
        ARTIFACT_DIR / "test_predictions.csv",
        index=False,
    )

    # Save confusion matrix
    class_names = sorted(y.unique())
    cm = confusion_matrix(
        y_test, y_pred, labels=class_names
    )
    display = ConfusionMatrixDisplay(
        confusion_matrix=cm,
        display_labels=class_names,
    )
    display.plot(xticks_rotation=90, values_format="d")
    plt.title("TabPFN Crop Recommendation - Test Confusion Matrix")
    plt.tight_layout()
    plt.savefig(
        ARTIFACT_DIR / "confusion_matrix.png",
        dpi=150,
        bbox_inches="tight",
    )
    plt.close()

    print("\n=== HELD-OUT TEST RESULTS ===")
    print(f"Accuracy:       {metrics['accuracy']:.4f}")
    print(f"Macro precision:{metrics['macro_precision']:.4f}")
    print(f"Macro recall:   {metrics['macro_recall']:.4f}")
    print(f"Macro F1:       {metrics['macro_f1']:.4f}")
    print(f"Weighted F1:    {metrics['weighted_f1']:.4f}")
    print(f"Training time:  {training_seconds:.2f} seconds")
    print(f"Test inference: {inference_seconds:.2f} seconds")

    print("\n=== PER-CLASS REPORT ===")
    print(
        classification_report(
            y_test, y_pred, zero_division=0
        )
    )

    print("\nSaved model:", MODEL_DIR / "tabpfn_crop_model.joblib")
    print("Saved metrics:", ARTIFACT_DIR / "evaluation_metrics.json")
    print("Saved predictions:", ARTIFACT_DIR / "test_predictions.csv")
    print("Saved confusion matrix:", ARTIFACT_DIR / "confusion_matrix.png")
    print("\nTraining and evaluation completed successfully.")


if __name__ == "__main__":
    main()
