
from pathlib import Path

import pandas as pd


# =====================================================
# LOAD DATASET
# =====================================================

BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data" / "raw" / "crop_production.csv"

if not DATA_PATH.exists():
    raise FileNotFoundError(
        f"Dataset not found: {DATA_PATH}"
    )

df = pd.read_csv(DATA_PATH)

if df.empty:
    raise ValueError("The dataset is empty.")


# =====================================================
# DATASET OVERVIEW
# =====================================================

print("\n========== DATASET OVERVIEW ==========")
print(f"File: {DATA_PATH}")
print(f"Rows: {len(df):,}")
print(f"Columns: {len(df.columns)}")
print(
    f"Memory usage: "
    f"{df.memory_usage(deep=True).sum() / (1024**2):.2f} MB"
)


# =====================================================
# COLUMN INFORMATION
# =====================================================

print("\n========== COLUMN NAMES ==========")
print(df.columns.tolist())

print("\n========== DATA TYPES ==========")
print(df.dtypes.to_string())


# =====================================================
# SAMPLE RECORDS
# =====================================================

print("\n========== FIRST 5 ROWS ==========")
print(df.head().to_string(index=False))


# =====================================================
# MISSING VALUES AND DUPLICATES
# =====================================================

print("\n========== MISSING VALUES ==========")
print(df.isnull().sum().to_string())

print("\n========== DUPLICATES ==========")
print(f"Exact duplicate rows: {df.duplicated().sum():,}")


# =====================================================
# NUMERIC SUMMARY
# =====================================================

print("\n========== NUMERIC SUMMARY ==========")

numeric_columns = df.select_dtypes(include="number").columns

if len(numeric_columns):
    print(df[numeric_columns].describe().to_string())
else:
    print("No numeric columns found.")


# =====================================================
# CATEGORICAL SUMMARY
# =====================================================

print("\n========== CATEGORICAL SUMMARY ==========")

categorical_columns = df.select_dtypes(
    include=["object", "category", "string"]
).columns

if len(categorical_columns):

    for col in categorical_columns:
        print(f"\n{col}:")
        print(f"Unique values: {df[col].nunique(dropna=True):,}")
        print(
            df[col]
            .value_counts(dropna=False)
            .head(10)
            .to_string()
        )
else:
    print("No categorical columns found.")


# =====================================================
# POSSIBLE TARGET: CROP
# =====================================================

print("\n========== POSSIBLE TARGET: CROP ==========")

crop_names = {"crop", "crop_name", "crop_names"}

crop_cols = [
    col for col in df.columns
    if str(col).strip().lower() in crop_names
]

if crop_cols:

    crop_col = crop_cols[0]

    print(f"Crop column: {crop_col}")
    print(f"Unique crops: {df[crop_col].nunique(dropna=True):,}")
    print(df[crop_col].value_counts().head(20).to_string())

else:
    print(
        "No standard crop column found. "
        "Inspect the column names above."
    )


# =====================================================
# POSSIBLE YEAR RANGE
# =====================================================

print("\n========== POSSIBLE YEAR RANGE ==========")

year_cols = [
    col for col in df.columns
    if "year" in str(col).lower()
]

if year_cols:

    for col in year_cols:
        years = pd.to_numeric(df[col], errors="coerce")

        print(
            f"{col}: {years.min()} to {years.max()}"
        )
else:
    print("No year column found.")


print("\n========== AUDIT COMPLETE ==========")
