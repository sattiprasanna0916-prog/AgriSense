
from pathlib import Path
import pandas as pd

DATA_PATH = Path("data/raw/crop_production.csv")

if not DATA_PATH.exists():
    raise FileNotFoundError(
        f"Dataset not found: {DATA_PATH.resolve()}"
    )

df = pd.read_csv(DATA_PATH)

print("\n========== DATASET OVERVIEW ==========")
print(f"File: {DATA_PATH.resolve()}")
print(f"Rows: {len(df):,}")
print(f"Columns: {len(df.columns)}")
print(f"Memory usage: {df.memory_usage(deep=True).sum() / (1024**2):.2f} MB")

print("\n========== COLUMN NAMES ==========")
print(df.columns.tolist())

print("\n========== DATA TYPES ==========")
print(df.dtypes.to_string())

print("\n========== FIRST 5 ROWS ==========")
print(df.head().to_string(index=False))

print("\n========== MISSING VALUES ==========")
print(df.isnull().sum().to_string())

print("\n========== DUPLICATES ==========")
print(f"Exact duplicate rows: {df.duplicated().sum():,}")

print("\n========== NUMERIC SUMMARY ==========")
print(df.describe(include="number").to_string())

print("\n========== CATEGORICAL SUMMARY ==========")
for col in df.select_dtypes(include=["object", "category"]).columns:
    print(f"\n{col}:")
    print(f"Unique values: {df[col].nunique(dropna=True):,}")
    print(df[col].value_counts(dropna=False).head(10).to_string())

print("\n========== POSSIBLE TARGET: CROP ==========")
crop_cols = [c for c in df.columns if c.strip().lower() in {"crop", "crop_name", "crop_names"}]
if crop_cols:
    crop_col = crop_cols[0]
    print(f"Crop column: {crop_col}")
    print(f"Unique crops: {df[crop_col].nunique(dropna=True):,}")
    print(df[crop_col].value_counts().head(20).to_string())
else:
    print("No standard crop column found. Inspect the column names above.")

print("\n========== POSSIBLE YEAR RANGE ==========")
year_cols = [c for c in df.columns if "year" in c.lower()]
for col in year_cols:
    years = pd.to_numeric(df[col], errors="coerce")
    print(f"{col}: {years.min()} to {years.max()}")

print("\n========== AUDIT COMPLETE ==========")
