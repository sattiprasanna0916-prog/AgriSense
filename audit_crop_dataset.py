
from pathlib import Path

import pandas as pd
import numpy as np


# =========================================================
# 1. DATASET PATH
# =========================================================

BASE_DIR = Path(__file__).resolve().parent

DATA_PATH = BASE_DIR / "data" / "raw" / "Crop_recommendation.csv"

if not DATA_PATH.exists():
    DATA_PATH = Path(
        r"C:\Users\satti\Documents\Crop_recommendation.csv"
    )

if not DATA_PATH.exists():
    raise FileNotFoundError(
        "Crop_recommendation.csv was not found. "
        "Update DATA_PATH to its actual location."
    )


# =========================================================
# 2. LOAD DATASET
# =========================================================

df = pd.read_csv(DATA_PATH)

expected = [
    "N",
    "P",
    "K",
    "temperature",
    "humidity",
    "ph",
    "rainfall"
]


# =========================================================
# 3. DATASET OVERVIEW
# =========================================================

print("\n========== DATASET OVERVIEW ==========")

print("File:", DATA_PATH.resolve())
print("Rows:", len(df))
print("Columns:", len(df.columns))
print("Column names:", df.columns.tolist())


# =========================================================
# 4. DATA TYPES
# =========================================================

print("\n========== DATA TYPES ==========")

print(df.dtypes.to_string())


# =========================================================
# 5. MISSING VALUES
# =========================================================

print("\n========== MISSING VALUES ==========")

print(df.isnull().sum().to_string())


# =========================================================
# 6. DUPLICATE ROWS
# =========================================================

print("\n========== DUPLICATE ROWS ==========")

duplicate_count = int(df.duplicated().sum())

print("Exact duplicate rows:", duplicate_count)


# =========================================================
# 7. CONFLICTING LABELS
# =========================================================

print("\n========== CONFLICTING LABELS ==========")

if all(col in df.columns for col in expected + ["label"]):

    # Convert feature columns to numeric for consistent grouping.
    feature_data = df[expected].apply(
        pd.to_numeric,
        errors="coerce"
    )

    valid_rows = feature_data.notna().all(axis=1) & df["label"].notna()

    conflict_data = feature_data.loc[valid_rows].copy()
    conflict_data["label"] = df.loc[valid_rows, "label"]

    conflicts = (
        conflict_data.groupby(expected, dropna=False)["label"]
        .nunique()
        .gt(1)
        .sum()
    )

    print(
        "Feature combinations with conflicting labels:",
        int(conflicts)
    )

else:
    print(
        "Cannot perform conflicting-label check. "
        "Required feature columns or 'label' are missing."
    )


# =========================================================
# 8. CROP DISTRIBUTION
# =========================================================

print("\n========== CROP DISTRIBUTION ==========")

if "label" in df.columns:

    counts = df["label"].value_counts(
        dropna=False
    ).sort_index()

    print(counts.to_string())

    print(
        "Number of crop classes:",
        df["label"].nunique(dropna=True)
    )

    if not counts.empty:
        print("Smallest class size:", counts.min())
        print("Largest class size:", counts.max())

else:
    print("WARNING: Target column 'label' not found.")


# =========================================================
# 9. NUMERIC SUMMARY
# =========================================================

print("\n========== NUMERIC SUMMARY ==========")

print(
    df.describe(include="all")
    .transpose()
    .to_string()
)


# =========================================================
# 10. INVALID NUMERIC VALUES
# =========================================================

print("\n========== INVALID NUMERIC VALUES ==========")

for col in expected:

    if col not in df.columns:
        print(f"{col}: MISSING COLUMN")
        continue

    values = pd.to_numeric(
        df[col],
        errors="coerce"
    )

    missing_or_non_numeric = int(values.isna().sum())

    infinite = int(
        np.isinf(
            values.dropna().to_numpy(dtype=float)
        ).sum()
    )

    print(
        f"{col}: "
        f"missing/non-numeric={missing_or_non_numeric}, "
        f"infinite={infinite}, "
        f"minimum={values.min()}, "
        f"maximum={values.max()}"
    )


# =========================================================
# 11. BASIC VALIDATION
# =========================================================

print("\n========== BASIC VALIDATION ==========")

expected_columns = set(expected + ["label"])

actual_columns = set(df.columns)

print(
    "Unexpected columns:",
    sorted(actual_columns - expected_columns)
)

print(
    "Missing expected columns:",
    sorted(expected_columns - actual_columns)
)


# =========================================================
# 12. FINAL STATUS
# =========================================================

print("\n========== AUDIT SUMMARY ==========")

print("Dataset audit completed successfully.")
print("Dataset rows:", len(df))
print("Dataset columns:", len(df.columns))
print("Exact duplicate rows:", duplicate_count)

print("\nAudit complete. No files or model artifacts were modified.")
