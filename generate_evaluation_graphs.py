
import json
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt
from sklearn.metrics import (
    accuracy_score,
    classification_report
)

# --------------------------------------------------
# 1. FILE PATHS
# --------------------------------------------------

PROJECT_DIR = Path(__file__).resolve().parent
ARTIFACTS_DIR = PROJECT_DIR / "artifacts"

PREDICTIONS_FILE = ARTIFACTS_DIR / "test_predictions.csv"
METRICS_FILE = ARTIFACTS_DIR / "evaluation_metrics.json"

OUTPUT_DIR = ARTIFACTS_DIR / "chapter9_graphs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# --------------------------------------------------
# 2. LOAD TEST PREDICTIONS AND EVALUATION JSON
# --------------------------------------------------

df = pd.read_csv(PREDICTIONS_FILE)

with open(METRICS_FILE, "r") as file:
    saved_metrics = json.load(file)

# Update these column names if your CSV uses different names
actual = df["actual_crop"].astype(str)
predicted = df["predicted_crop"].astype(str)

labels = sorted(actual.unique())

# --------------------------------------------------
# 3. CALCULATE EVALUATION METRICS
# --------------------------------------------------

accuracy = accuracy_score(actual, predicted)

report = classification_report(
    actual,
    predicted,
    labels=labels,
    output_dict=True,
    zero_division=0
)

macro_precision = report["macro avg"]["precision"]
macro_recall = report["macro avg"]["recall"]
macro_f1 = report["macro avg"]["f1-score"]
weighted_f1 = report["weighted avg"]["f1-score"]

print("\n========== TABPFN EVALUATION RESULTS ==========")
print(f"Total test records : {len(df)}")
print(f"Correct predictions: {(actual == predicted).sum()}")
print(f"Incorrect predictions: {(actual != predicted).sum()}")
print(f"Accuracy           : {accuracy * 100:.2f}%")
print(f"Macro Precision    : {macro_precision * 100:.2f}%")
print(f"Macro Recall       : {macro_recall * 100:.2f}%")
print(f"Macro F1-Score     : {macro_f1 * 100:.2f}%")
print(f"Weighted F1-Score  : {weighted_f1 * 100:.2f}%")

# Verify against the saved evaluation JSON
print("\n========== JSON VALIDATION ==========")

checks = {
    "Accuracy": (accuracy, saved_metrics["accuracy"]),
    "Macro Precision": (
        macro_precision, saved_metrics["macro_precision"]
    ),
    "Macro Recall": (
        macro_recall, saved_metrics["macro_recall"]
    ),
    "Macro F1": (macro_f1, saved_metrics["macro_f1"]),
    "Weighted F1": (
        weighted_f1, saved_metrics["weighted_f1"]
    )
}

for name, (calculated, saved) in checks.items():
    matched = abs(calculated - saved) < 1e-8
    print(f"{name}: {'MATCH' if matched else 'MISMATCH'}")

# --------------------------------------------------
# 4. FIGURE 9.3.1 - ACCURACY EVALUATION
# --------------------------------------------------

correct = int((actual == predicted).sum())
incorrect = len(df) - correct

fig, ax = plt.subplots(figsize=(8, 5))

bars = ax.bar(
    ["Correct Predictions", "Incorrect Predictions"],
    [correct, incorrect]
)

ax.set_title(
    "TabPFN Accuracy Evaluation",
    fontsize=15,
    fontweight="bold"
)
ax.set_ylabel("Number of Test Records")
ax.set_ylim(0, len(df) * 1.15)

for bar, value in zip(bars, [correct, incorrect]):
    ax.text(
        bar.get_x() + bar.get_width() / 2,
        bar.get_height() + 2,
        str(value),
        ha="center",
        fontsize=11
    )

ax.text(
    0.5, 0.90,
    f"Accuracy = {accuracy * 100:.2f}%",
    transform=ax.transAxes,
    ha="center",
    fontsize=12
)

plt.tight_layout()
plt.savefig(
    OUTPUT_DIR / "Fig_9_3_1_Accuracy.png",
    dpi=300,
    bbox_inches="tight"
)
plt.show()
plt.close()

# --------------------------------------------------
# 5. FIGURE 9.3.2 - PRECISION EVALUATION
# --------------------------------------------------

# --------------------------------------------------
# 6. FIGURE 9.3.3 - RECALL EVALUATION
# --------------------------------------------------

# --------------------------------------------------
# 7. FIGURE 9.3.4 - F1-SCORE EVALUATION
# --------------------------------------------------

def create_classwise_graph(
    metric,
    title,
    filename,
    ylabel
):
    values = [
        report[crop][metric] * 100
        for crop in labels
    ]

    macro_value = report["macro avg"][metric] * 100

    fig, ax = plt.subplots(figsize=(12, 6))

    bars = ax.bar(labels, values)

    ax.axhline(
        y=macro_value,
        linestyle="--",
        label=f"Macro Average: {macro_value:.2f}%"
    )

    ax.set_title(
        title,
        fontsize=15,
        fontweight="bold"
    )
    ax.set_xlabel("Crop Class")
    ax.set_ylabel(ylabel)
    ax.set_ylim(0, 110)

    plt.xticks(rotation=45, ha="right")

    for bar, value in zip(bars, values):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            value + 1,
            f"{value:.1f}",
            ha="center",
            va="bottom",
            fontsize=8,
            rotation=90
        )

    ax.legend()
    plt.tight_layout()

    plt.savefig(
        OUTPUT_DIR / filename,
        dpi=300,
        bbox_inches="tight"
    )

    plt.show()
    plt.close()


create_classwise_graph(
    "precision",
    "TabPFN Precision Evaluation",
    "Fig_9_3_2_Precision.png",
    "Precision (%)"
)

create_classwise_graph(
    "recall",
    "TabPFN Recall Evaluation",
    "Fig_9_3_3_Recall.png",
    "Recall (%)"
)

create_classwise_graph(
    "f1-score",
    "TabPFN F1-Score Evaluation",
    "Fig_9_3_4_F1_Score.png",
    "F1-Score (%)"
)

# --------------------------------------------------
# 8. SAVE EVALUATION SUMMARY
# --------------------------------------------------

summary = pd.DataFrame({
    "Metric": [
        "Accuracy",
        "Macro Precision",
        "Macro Recall",
        "Macro F1-Score",
        "Weighted F1-Score"
    ],
    "Score (%)": [
        accuracy * 100,
        macro_precision * 100,
        macro_recall * 100,
        macro_f1 * 100,
        weighted_f1 * 100
    ]
})

summary.to_csv(
    OUTPUT_DIR / "evaluation_summary.csv",
    index=False
)

print("\nAll four graphs generated successfully!")
print("Output folder:", OUTPUT_DIR)
