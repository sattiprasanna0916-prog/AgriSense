
import joblib
import shap
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from pathlib import Path
from sklearn.model_selection import train_test_split

# --------------------------------------------------
# 1. PROJECT PATHS
# --------------------------------------------------

PROJECT_DIR = Path(__file__).resolve().parent

DATASET_PATH = PROJECT_DIR / "data" / "raw" / "Crop_recommendation.csv"
MODEL_PATH = PROJECT_DIR / "models" / "tabpfn_crop_model.joblib"

OUTPUT_DIR = PROJECT_DIR / "artifacts" / "chapter9_shap_graphs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# --------------------------------------------------
# 2. LOAD DATASET AND TRAINED MODEL
# --------------------------------------------------

print("Loading dataset...")

df = pd.read_csv(DATASET_PATH)

features = [
    "N",
    "P",
    "K",
    "temperature",
    "humidity",
    "ph",
    "rainfall"
]

X = df[features]
y = df["label"]

print("Loading existing TabPFN model...")
model = joblib.load(MODEL_PATH)

# Use the same split as the original evaluation
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42,
    stratify=y
)

print("Training records:", len(X_train))
print("Testing records:", len(X_test))

# --------------------------------------------------
# 3. SELECT BACKGROUND AND EXPLANATION SAMPLES
# --------------------------------------------------

# Background data represents reference input conditions
background = X_train.sample(
    n=min(20, len(X_train)),
    random_state=42
)

# Explain a small representative subset of test records
explain_data = X_test.sample(
    n=min(20, len(X_test)),
    random_state=42
)

# --------------------------------------------------
# 4. CREATE SHAP EXPLAINER
# --------------------------------------------------

print("\nCreating SHAP explainer...")

explainer = shap.Explainer(
    model.predict_proba,
    background,
    algorithm="permutation"
)

print("Calculating SHAP values...")
print("This may take some time because TabPFN inference is computationally expensive.")

shap_values = explainer(
    explain_data,
    max_evals=30
)

values = np.asarray(shap_values.values)
base_values = np.asarray(shap_values.base_values)

print("SHAP values shape:", values.shape)

# Expected shape: samples x features x classes
# Handle alternate output ordering if returned
if values.ndim != 3:
    raise ValueError(
        f"Unexpected SHAP output shape: {values.shape}"
    )

if values.shape[1] == len(features):
    pass
elif values.shape[2] == len(features):
    values = np.transpose(values, (0, 2, 1))
else:
    raise ValueError(
        "Could not identify the feature dimension in SHAP values."
    )

# --------------------------------------------------
# 5. FIGURE 9.4.1 - SHAP WATERFALL PLOT
# --------------------------------------------------

# Explain the first selected test record
sample_index = 0

sample = explain_data.iloc[sample_index:sample_index + 1]

# Get the predicted crop
probabilities = model.predict_proba(sample)
predicted_class_index = int(np.argmax(probabilities[0]))

class_names = np.asarray(model.classes_)
predicted_crop = class_names[predicted_class_index]

print("\nSelected sample prediction:", predicted_crop)

# Extract SHAP contributions for the predicted class
sample_values = values[
    sample_index, :, predicted_class_index
]

# Select the base value for the predicted class
if base_values.ndim == 2:
    sample_base_value = base_values[
        sample_index, predicted_class_index
    ]
else:
    sample_base_value = base_values[sample_index]

waterfall_explanation = shap.Explanation(
    values=sample_values,
    base_values=sample_base_value,
    data=sample.iloc[0].values,
    feature_names=features
)

plt.figure(figsize=(10, 6))

shap.plots.waterfall(
    waterfall_explanation,
    show=False
)

plt.title(
    f"SHAP Feature Contributions for {predicted_crop}",
    fontsize=14,
    fontweight="bold"
)

plt.tight_layout()

plt.savefig(
    OUTPUT_DIR / "Fig_9_4_1_SHAP_Waterfall.png",
    dpi=300,
    bbox_inches="tight"
)

plt.show()
plt.close()

# --------------------------------------------------
# 6. FIGURE 9.4.2 - GLOBAL SHAP FEATURE IMPORTANCE
# --------------------------------------------------

# Average absolute SHAP values across explained samples
# and all crop-class outputs
global_importance = np.mean(
    np.abs(values),
    axis=(0, 2)
)

importance_df = pd.DataFrame({
    "Feature": features,
    "Mean Absolute SHAP Value": global_importance
})

importance_df = importance_df.sort_values(
    by="Mean Absolute SHAP Value",
    ascending=True
)

plt.figure(figsize=(10, 6))

bars = plt.barh(
    importance_df["Feature"],
    importance_df["Mean Absolute SHAP Value"]
)

plt.xlabel("Mean Absolute SHAP Value")
plt.ylabel("Agricultural Parameters")

plt.title(
    "Global SHAP Feature Importance",
    fontsize=14,
    fontweight="bold"
)

for bar in bars:
    width = bar.get_width()
    plt.text(
        width,
        bar.get_y() + bar.get_height() / 2,
        f" {width:.4f}",
        va="center",
        fontsize=9
    )

plt.tight_layout()

plt.savefig(
    OUTPUT_DIR / "Fig_9_4_2_SHAP_Feature_Importance.png",
    dpi=300,
    bbox_inches="tight"
)

plt.show()
plt.close()

# --------------------------------------------------
# 7. SAVE FEATURE IMPORTANCE VALUES
# --------------------------------------------------

importance_df.sort_values(
    by="Mean Absolute SHAP Value",
    ascending=False
).to_csv(
    OUTPUT_DIR / "shap_feature_importance.csv",
    index=False
)

print("\nSHAP graphs generated successfully!")
print("Output directory:", OUTPUT_DIR)

print("\nGlobal feature importance:")
print(
    importance_df.sort_values(
        by="Mean Absolute SHAP Value",
        ascending=False
    ).to_string(index=False)
)
