
import json
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
ARTIFACTS = BASE_DIR / "artifacts"

with (ARTIFACTS / "evaluation_metrics.json").open(
    encoding="utf-8"
) as file:
    tabpfn = json.load(file)

with (ARTIFACTS / "random_forest_metrics.json").open(
    encoding="utf-8"
) as file:
    random_forest = json.load(file)

metrics = [
    ("Accuracy", "accuracy"),
    ("Macro Precision", "macro_precision"),
    ("Macro Recall", "macro_recall"),
    ("Macro F1", "macro_f1"),
    ("Weighted F1", "weighted_f1"),
    ("Training Time (seconds)", "training_seconds"),
    ("Test Inference Time (seconds)", "inference_seconds_for_test_set"),
]

rows = []
for label, key in metrics:
    rows.append({
        "Metric": label,
        "TabPFN": tabpfn.get(key),
        "Random Forest": random_forest.get(key),
    })

comparison = pd.DataFrame(rows)
output_path = ARTIFACTS / "model_comparison.csv"
comparison.to_csv(output_path, index=False)

print("\n=== MODEL COMPARISON ===")
print(comparison.to_string(index=False))
print(f"\nSaved comparison to: {output_path}")
