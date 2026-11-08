
from pathlib import Path
import joblib
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.svm import SVC
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score
)

# --------------------------------------------------
# 1. Project paths
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent

DATA_PATH = BASE_DIR / "data" / "raw" / "Crop_recommendation.csv"
MODEL_PATH = BASE_DIR / "models" / "tabpfn_crop_model.joblib"

OUTPUT_DIR = BASE_DIR / "results" / "model_comparison"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# --------------------------------------------------
# 2. Load dataset
# --------------------------------------------------

print("Loading agricultural dataset...")

df = pd.read_csv(DATA_PATH)

features = [
    "N", "P", "K",
    "temperature", "humidity",
    "ph", "rainfall"
]

X = df[features]
y = df["label"]

print("Dataset records:", len(df))
print("Number of crop classes:", y.nunique())

# --------------------------------------------------
# 3. Same 80:20 stratified split
# --------------------------------------------------

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y
)

print("\nTraining records:", len(X_train))
print("Testing records:", len(X_test))

# --------------------------------------------------
# 4. Load existing TabPFN model
# --------------------------------------------------

print("\nLoading existing TabPFN model...")

if not MODEL_PATH.exists():
    raise FileNotFoundError(
        f"TabPFN model not found: {MODEL_PATH}"
    )

tabpfn_model = joblib.load(MODEL_PATH)

# --------------------------------------------------
# 5. Define comparison algorithms
# --------------------------------------------------

models = {
    "TabPFN": tabpfn_model,

    "Random Forest": RandomForestClassifier(
        n_estimators=300,
        random_state=42,
        n_jobs=-1
    ),

    "Decision Tree": DecisionTreeClassifier(
        random_state=42
    ),

    "SVM": Pipeline([
        ("scaler", StandardScaler()),
        ("classifier", SVC(
            kernel="rbf",
            C=1.0,
            random_state=42
        ))
    ])
}

# --------------------------------------------------
# 6. Evaluate all models
# --------------------------------------------------

results = []

for model_name, model in models.items():

    print(f"\nEvaluating {model_name}...")

    # Do not retrain the saved TabPFN model
    if model_name != "TabPFN":
        model.fit(X_train, y_train)

    predictions = model.predict(X_test)

    accuracy = accuracy_score(y_test, predictions)
    precision = precision_score(
        y_test, predictions,
        average="macro",
        zero_division=0
    )
    recall = recall_score(
        y_test, predictions,
        average="macro",
        zero_division=0
    )
    f1 = f1_score(
        y_test, predictions,
        average="macro",
        zero_division=0
    )

    results.append({
        "Model": model_name,
        "Accuracy": accuracy * 100,
        "Precision": precision * 100,
        "Recall": recall * 100,
        "F1-Score": f1 * 100
    })

    print(f"Accuracy:  {accuracy * 100:.2f}%")
    print(f"Precision: {precision * 100:.2f}%")
    print(f"Recall:    {recall * 100:.2f}%")
    print(f"F1-Score:  {f1 * 100:.2f}%")

# --------------------------------------------------
# 7. Save comparison results
# --------------------------------------------------

results_df = pd.DataFrame(results)

csv_path = OUTPUT_DIR / "model_comparison_results.csv"
results_df.to_csv(csv_path, index=False)

print("\nMODEL COMPARISON RESULTS")
print(results_df.round(2).to_string(index=False))

# --------------------------------------------------
# 8. Generate grouped bar chart
# --------------------------------------------------

metrics = ["Accuracy", "Precision", "Recall", "F1-Score"]

model_names = results_df["Model"].tolist()

x = np.arange(len(metrics))
bar_width = 0.19

fig, ax = plt.subplots(figsize=(12, 7))

colors = [
    "#718096",
    "#319795",
    "#3182CE",
    "#E09F3E"
]

for i, model_name in enumerate(model_names):

    values = results_df.loc[
        results_df["Model"] == model_name,
        metrics
    ].values.flatten()

    positions = x + (i - 1.5) * bar_width

    bars = ax.bar(
        positions,
        values,
        bar_width,
        label=model_name,
        color=colors[i],
        edgecolor="white",
        linewidth=1
    )

    for bar, value in zip(bars, values):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.8,
            f"{value:.1f}",
            ha="center",
            va="bottom",
            fontsize=8
        )

ax.set_title(
    "Comparative Performance of Machine Learning Algorithms",
    fontsize=15,
    fontweight="bold",
    pad=18
)

ax.set_xlabel("Evaluation Metrics", fontsize=11)
ax.set_ylabel("Performance (%)", fontsize=11)

ax.set_xticks(x)
ax.set_xticklabels(metrics)

ax.set_ylim(0, 110)
ax.set_yticks(np.arange(0, 101, 10))

ax.grid(axis="y", linestyle="--", alpha=0.3)
ax.set_axisbelow(True)

ax.legend(
    loc="upper center",
    bbox_to_anchor=(0.5, -0.10),
    ncol=4,
    frameon=False
)

plt.tight_layout()

graph_path = OUTPUT_DIR / "model_comparison_graph.png"

plt.savefig(
    graph_path,
    dpi=300,
    bbox_inches="tight"
)

plt.show()

print("\nComparison completed!")
print("CSV saved:", csv_path)
print("Graph saved:", graph_path)
