
from pathlib import Path

import pandas as pd


# =========================================================
# 1. DATASET PATH
# =========================================================

BASE_DIR = Path(__file__).resolve().parent

DATA_PATH = BASE_DIR / "data" / "raw" / "crop_production.csv"

if not DATA_PATH.exists():
    raise FileNotFoundError(
        f"Historical production dataset not found: {DATA_PATH}\n"
        "Check the data/raw folder and filename."
    )


# =========================================================
# 2. LOAD DATASET
# =========================================================

df = pd.read_csv(DATA_PATH)

print("\n========== DATASET OVERVIEW ==========")

print("File:", DATA_PATH.resolve())
print("Rows:", len(df))
print("Columns:", len(df.columns))
print("Column names:", df.columns.tolist())


# =========================================================
# 3. REQUIRED COLUMN VALIDATION
# =========================================================

required_columns = [
    "State_Name",
    "District_Name",
    "Crop_Year",
    "Season",
    "Crop",
    "Area",
    "Production"
]

missing_columns = [
    col for col in required_columns
    if col not in df.columns
]

if missing_columns:
    raise ValueError(
        f"Required columns missing from dataset: {missing_columns}"
    )


# =========================================================
# 4. NUMERIC DATA VALIDATION
# =========================================================

for col in ["Area", "Production", "Crop_Year"]:
    df[col] = pd.to_numeric(
        df[col],
        errors="coerce"
    )


# =========================================================
# 5. MISSING PRODUCTION
# =========================================================

print("\n========== MISSING PRODUCTION ==========")

missing = df[df["Production"].isna()]

print(f"Missing records: {len(missing):,}")

if not missing.empty:
    print(missing.head(10).to_string(index=False))


# =========================================================
# 6. ZERO PRODUCTION
# =========================================================

print("\n========== ZERO PRODUCTION ==========")

zero = df[df["Production"].eq(0)]

print(f"Zero-production records: {len(zero):,}")

if not zero.empty:
    print(zero.head(10).to_string(index=False))


# =========================================================
# 7. AREA AND PRODUCTION EXTREMES
# =========================================================

print("\n========== AREA AND PRODUCTION EXTREMES ==========")

for col in ["Area", "Production"]:

    print(f"\n{col}:")

    valid_values = df[col].dropna()

    if valid_values.empty:
        print("No valid numeric values found.")
    else:
        print(valid_values.nlargest(10).to_string())


# =========================================================
# 8. POTENTIAL DUPLICATE KEYS
# =========================================================

print("\n========== POTENTIAL DUPLICATE KEYS ==========")

keys = [
    "State_Name",
    "District_Name",
    "Crop_Year",
    "Season",
    "Crop"
]

duplicate_keys = df.duplicated(
    subset=keys,
    keep=False
)

print(
    "Records sharing a district/year/season/crop key:",
    f"{duplicate_keys.sum():,}"
)

if duplicate_keys.any():

    print(
        df.loc[
            duplicate_keys,
            keys + ["Area", "Production"]
        ]
        .head(15)
        .to_string(index=False)
    )


# =========================================================
# 9. RECORD COUNTS BY YEAR
# =========================================================

print("\n========== RECORD COUNTS BY YEAR ==========")

year_counts = df.groupby(
    "Crop_Year",
    dropna=False
).size()

print(year_counts.to_string())


# =========================================================
# 10. PRODUCTION MISSINGNESS BY SEASON
# =========================================================

print("\n========== PRODUCTION MISSINGNESS BY SEASON ==========")

season_quality = (
    df.groupby("Season", dropna=False)["Production"]
    .agg(
        total_records="size",
        available_production="count"
    )
)

season_quality["missing_production"] = (
    season_quality["total_records"]
    - season_quality["available_production"]
)

print(season_quality.to_string())


# =========================================================
# 11. FINAL AUDIT SUMMARY
# =========================================================

print("\n========== AUDIT SUMMARY ==========")

print("Total records:", len(df))
print("Missing production:", len(missing))
print("Zero production:", len(zero))
print(
    "Potential duplicate-key records:",
    int(duplicate_keys.sum())
)

print("\nHistorical production data quality audit complete.")
print("No dataset files or model artifacts were modified.")
