
import os
import joblib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.svm import SVC
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler, label_binarize
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_curve,
    auc
)

# --------------------------------------------------
# 1. Load dataset and create the same train-test split
# --------------------------------------------------

DATA_PATH = r"C:\Users\satti\Documents\Crop_recommendation.csv"
MODEL_PATH = "models/tabpfn_crop_model.joblib"
OUTPUT_DIR = "comparison_graphs"

os.makedirs(OUTPUT_DIR, exist_ok=True)

df = pd.read_csv(DATA_PATH)

X = df.drop("label", axis=1)
y = df["label"]

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y
)

print("Training records:", len(X_train))
print("Testing records:", len(X_test))

# --------------------------------------------------
# 2. Load the existing TabPFN model
# --------------------------------------------------

tabpfn = joblib.load(MODEL_PATH)

# --------------------------------------------------
# 3. Train baseline models
# --------------------------------------------------

models = {
    "TabPFN": tabpfn,

    "Random Forest": RandomForestClassifier(
        n_estimators=100,
        random_state=42
    ),

    "Decision Tree": DecisionTreeClassifier(
        random_state=42
    ),

    "SVM": make_pipeline(
        StandardScaler(),
        SVC(probability=True, random_state=42)
    )
}

# --------------------------------------------------
# 4. Generate predictions and probabilities
# --------------------------------------------------

results = {}
probabilities = {}

for name, model in models.items():

    print(f"\nEvaluating {name}...")

    if name != "TabPFN":
        model.fit(X_train, y_train)

    predictions = model.predict(X_test)
    results[name] = predictions

    if not hasattr(model, "predict_proba"):
        raise RuntimeError(f"{name} does not support predict_proba.")

    probabilities[name] = model.predict_proba(X_test)

# --------------------------------------------------
# 5. Calculate evaluation metrics
# --------------------------------------------------

metrics = {}

for name, predictions in results.items():

    metrics[name] = {
        "Accuracy": accuracy_score(y_test, predictions),
        "Macro Precision": precision_score(
            y_test, predictions, average="macro", zero_division=0
        ),
        "Macro Recall": recall_score(
            y_test, predictions, average="macro", zero_division=0
        ),
        "Macro F1-Score": f1_score(
            y_test, predictions, average="macro", zero_division=0
        )
    }

metrics_df = pd.DataFrame(metrics).T
metrics_df.to_csv(
    os.path.join(OUTPUT_DIR, "comparison_metrics.csv")
)

print("\nCOMPARATIVE RESULTS")
print(metrics_df.round(4))

# --------------------------------------------------
# 6. Generate four metric comparison graphs
# --------------------------------------------------

metric_names = [
    ("Accuracy", "Accuracy Comparison"),
    ("Macro Precision", "Precision Comparison"),
    ("Macro Recall", "Recall Comparison"),
    ("Macro F1-Score", "F1-Score Comparison")
]

for metric, title in metric_names:

    plt.figure(figsize=(9, 5))

    values = metrics_df[metric] * 100

    bars = plt.bar(values.index, values.values)

    plt.title(title)
    plt.ylabel("Score (%)")
    plt.xlabel("Classification Algorithms")
    plt.ylim(0, 105)
    plt.xticks(rotation=15)

    for bar, value in zip(bars, values.values):
        plt.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 1,
            f"{value:.2f}%",
            ha="center"
        )

    plt.tight_layout()

    filename = metric.lower().replace(" ", "_").replace("-", "_")
    plt.savefig(
        os.path.join(OUTPUT_DIR, filename + ".png"),
        dpi=300,
        bbox_inches="tight"
    )

    plt.close()

# --------------------------------------------------
# 7. Generate macro-average multiclass ROC curves
# --------------------------------------------------

classes = np.unique(y_test)
y_test_binary = label_binarize(y_test, classes=classes)

plt.figure(figsize=(9, 7))

for name, model in models.items():

    model_classes = model.classes_ if hasattr(model, "classes_") else None

    if model_classes is None or not np.array_equal(model_classes, classes):
        raise ValueError(
            f"{name}: model class order does not match dataset classes. "
            "Check the saved TabPFN model's label encoding."
        )

    y_prob = probabilities[name]

    # Calculate one-vs-rest ROC curve for each crop class
    all_fpr = np.unique(np.concatenate([
        roc_curve(y_test_binary[:, i], y_prob[:, i])[0]
        for i in range(len(classes))
    ]))

    mean_tpr = np.zeros_like(all_fpr)

    for i in range(len(classes)):
        fpr, tpr, _ = roc_curve(
            y_test_binary[:, i],
            y_prob[:, i]
        )
        mean_tpr += np.interp(all_fpr, fpr, tpr)

    mean_tpr /= len(classes)

    macro_auc = auc(all_fpr, mean_tpr)

    plt.plot(
        all_fpr,
        mean_tpr,
        label=f"{name} (Macro AUC = {macro_auc:.4f})"
    )

plt.plot([0, 1], [0, 1], "k--", label="Random Classifier")

plt.title("Macro-Average ROC-AUC Comparison")
plt.xlabel("False Positive Rate")
plt.ylabel("True Positive Rate")
plt.legend(loc="lower right")
plt.grid(alpha=0.3)
plt.tight_layout()

plt.savefig(
    os.path.join(OUTPUT_DIR, "roc_auc_comparison.png"),
    dpi=300,
    bbox_inches="tight"
)

plt.close()

print("\nAll five graphs generated successfully.")
print("Output folder:", OUTPUT_DIR)
